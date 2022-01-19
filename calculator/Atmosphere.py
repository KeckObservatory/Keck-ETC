# Copyright (c) 2022, W. M. Keck Observatory
# All rights reserved.

# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. 


from astropy import units as u
from astropy.table import Table
import yaml
from os import listdir
from numpy import arange, zeros
# Including scipy introduces an additional dependency to project, but is significantly faster implementing manually
from scipy.interpolate import RegularGridInterpolator
from warnings import warn



class atmosphere:

    global _CONFIG_FILEPATH; _CONFIG_FILEPATH = 'calculator/atmosphere/atmosphere_config.yaml'

    def _mount_config(self, config_path):
        # From https://www.geeksforgeeks.org/convert-nested-python-dictionary-to-object/
        def _dict2obj(d):
            # If list, recursively unpack
            if isinstance(d, list):
                d = [_dict2obj(x) for x in d]
            # If not list or dictionary, return object
            if not isinstance(d, dict):
                return d
            # Otherwise, create dummy object
            class Foo:
                pass
            obj = Foo()
            # Loop over dictionary items and add to object
            for x in d:
                obj.__dict__[x] = _dict2obj(d[x])
            return obj
        # Open config file, convert & mount to self
        config = yaml.safe_load(open(config_path))
        config = _dict2obj(config)
        self.config = config


    def _load_files(self):
        self._water_vapor_index = [u.Quantity(x).to(u.mm).value for x in self.config.water_vapor_index] * u.mm
        self._airmass_index = u.Quantity(self.config.airmass_index)
        self.config.wavelength_index = [u.Quantity(x).to(u.angstrom) for x in self.config.wavelength_index]
        self._wavelength_index = arange(
            u.Quantity(self.config.wavelength_index[0]).value,
            u.Quantity(self.config.wavelength_index[1]).value,
            u.Quantity(self.config.wavelength_index[2]).value
        ) * u.angstrom  # np.arange doesn't support units, see https://github.com/astropy/astropy/issues/11582
        self._transmission = zeros([len(self._airmass_index), len(self._water_vapor_index), len(self._wavelength_index)])
        self._emission = zeros([len(self._airmass_index), len(self._water_vapor_index), len(self._wavelength_index)])
        # Iterate through directory, filling in self._transmission and self._emission arrays
        for i, filename in enumerate(listdir(self.config.file_directory)):
            #print('\rATMOSPHERE: Reading file '+str(i+1)+'/'+str(len(listdir(self.config.file_directory))), end='')
            try:
                if filename.startswith(self.config.transmission_filepath):
                    data = Table.read(self.config.file_directory+'/'+filename, format='fits')
                    self._transmission[
                        [x == u.Quantity(data.meta['AIRMASS']) for x in self._airmass_index], 
                        [x == u.Quantity(data.meta['VAPOR']) for x in self._water_vapor_index],
                        :
                    ] = data['transmission'].to('')
                if filename.startswith(self.config.emission_filepath):
                    data = Table.read(self.config.file_directory+'/'+filename, format='fits')
                    self._emission[
                        [x == u.Quantity(data.meta['AIRMASS']) for x in self._airmass_index], 
                        [x == u.Quantity(data.meta['VAPOR']) for x in self._water_vapor_index], 
                        :
                    ] = data['flux'].to('photon/(s arcsec^2 nm m^2)')
            except ValueError:
                raise ValueError('ERROR: In atmosphere._load_files() -- invalid file contents')
        #print()  # newline for console output


    def _validate_config(self):
        # Throw errors if config file doesn't conform to requirements


        # Check that all required fields exist and are spelled correctly
        try:
            _ = u.Quantity(self.config.defaults.seeing)
            _ = u.Quantity(self.config.defaults.airmass)
            _ = u.Quantity(self.config.defaults.water_vapor)
            _ = self.config.file_directory
            _ = self.config.emission_filepath
            _ = self.config.transmission_filepath
            _ = self.config.airmass_index
            _ = self.config.water_vapor_index
            _ = self.config.wavelength_index
        except:
            raise ValueError('ERROR: In atmosphere_config.yaml -- invalid configuration file, missing required value')

        # Check defaults.water_vapor and water_vapor_index
        test_wvi = [u.Quantity(x) for x in self.config.water_vapor_index]
        if not test_wvi == sorted(test_wvi):
            raise ValueError('ERROR: In atmosphere_config.yaml -- water_vapor_index is not in ascending order')
        if not test_wvi[0] <= u.Quantity(self.config.defaults.water_vapor) <= test_wvi[-1]:
            raise ValueError('ERROR: In atmosphere_config.yaml -- default water vapor is outside bounds of water_vapor_index')
        
        # Check defaults.airmass and airmass_index
        test_ami = [u.Quantity(x) for x in self.config.airmass_index]
        if not test_ami == sorted(test_ami):
            raise ValueError('ERROR: In atmosphere_config.yaml -- airmass_index is not in ascending order')
        if not test_ami[0] <= u.Quantity(self.config.defaults.airmass) <= test_ami[-1]:
            raise ValueError('ERROR: In atmosphere_config.yaml -- default airmass is outside bounds of airmass_index')

        # Check wavelength_index
        test_wi = [u.Quantity(x) for x in self.config.wavelength_index]
        if len(test_wi) != 3:
            raise ValueError('ERROR: In atmosphere_config.yaml -- wavelength_index does not have length == 3')
        if not (all([x > 0*u.nm for x in test_wi]) and test_wi[2] < (test_wi[1] - test_wi[0])):
            raise ValueError('ERROR: In atmosphere_config.yaml -- wavelength_index does not match format (start, end, step)')

        # Check emission_filepath and emission files
        test_em = [x for x in listdir(self.config.file_directory) if x.startswith(self.config.emission_filepath)]
        if not test_em:
            raise ValueError('ERROR: In atmosphere_config.yaml -- file_directory or emission_filepath is invalid, no matching files')
        try:
            pass  # Fix validation later -- too slow!
            # if not all([u.Quantity(Table.read(self.config.file_directory+'/'+x, format='ascii.ecsv', data_end=10).meta['water_vapor']) in test_wvi for x in test_em]):
            #     raise ValueError('ERROR: In atmosphere_config.yaml -- File matching emission_filepath has water_vapor that does not match water_vapor_index')
            # if not all([u.Quantity(Table.read(self.config.file_directory+'/'+x, format='ascii.ecsv', data_end=10).meta['airmass']) in test_ami for x in test_em]):
            #     raise ValueError('ERROR: In atmosphere_config.yaml -- File matching emission_filepath has airmass that does not match airmass_index')
        except:
            raise ValueError('ERROR: In atmosphere_config.yaml -- File matching emission_filepath does not have a valid ECSV file header, check metadata')

        # Check transmission_filepath and transmission files
        test_tr = [x for x in listdir(self.config.file_directory) if x.startswith(self.config.transmission_filepath)]
        if not test_tr:
            raise ValueError('ERROR: In atmosphere_config.yaml -- file_directory or transmission_filepath is invalid, no matching files')
        try:
            pass  # Fix validation later -- too slow!
            # if not all([u.Quantity(Table.read(self.config.file_directory+'/'+x, format='ascii.ecsv', data_end=10).meta['water_vapor']) in test_wvi for x in test_tr]):
            #     raise ValueError('ERROR: In atmosphere_config.yaml -- File matching transmission_filepath has water_vapor that does not match water_vapor_index')
            # if not all([u.Quantity(Table.read(self.config.file_directory+'/'+x, format='ascii.ecsv', data_end=10).meta['airmass']) in test_ami for x in test_tr]):
            #     raise ValueError('ERROR: In atmosphere_config.yaml -- File matching transmission_filepath has airmass that does not match airmass_index')
        except:
            raise ValueError('ERROR: In atmosphere_config.yaml -- File matching transmission_filepath does not have a valid ECSV file header, check metadata')

        

    def reset_parameters(self):
        
        self.seeing = u.Quantity(self.config.defaults.seeing)

        self.airmass = u.Quantity(self.config.defaults.airmass)

        self.water_vapor = u.Quantity(self.config.defaults.water_vapor)


    def __init__(self):
        self._mount_config(_CONFIG_FILEPATH)

        self._validate_config()

        self.reset_parameters()

        self._load_files()


    def get_transmission(self, wavelengths):

        results = zeros(len(wavelengths))

        # Check for and remove out-of-bounds wavelengths to avoid RegularGridInterpolator throwing errors
        wavelengths_trim = wavelengths[(self._wavelength_index[0] <= wavelengths) & (wavelengths <= self._wavelength_index[-1])]
        # If results are outside the wavelength bounds, return 0
        results[(self._wavelength_index[0] > wavelengths) | (wavelengths > self._wavelength_index[-1])] = 0

        # Perform trilinear interpolation to find transmission values
        interpolation = RegularGridInterpolator( (self._airmass_index, self._water_vapor_index, self._wavelength_index), self._transmission )
        interpolation = interpolation([[self.airmass.value, self.water_vapor.to(u.mm).value, λ] for λ in wavelengths_trim.to(u.angstrom).value])
        # Save interpolation values to results
        results[(self._wavelength_index[0] <= wavelengths) & (wavelengths <= self._wavelength_index[-1])] = interpolation
        return results * u.Unit('')


    def get_emission(self, wavelengths):
        results = zeros(len(wavelengths))

        # Check for and remove out-of-bounds wavelengths to avoid RegularGridInterpolator throwing errors
        wavelengths_trim = wavelengths[(self._wavelength_index[0] <= wavelengths) & (wavelengths <= self._wavelength_index[-1])]
        # If results are outside the wavelength bounds, return 0
        results[(self._wavelength_index[0] > wavelengths) | (wavelengths > self._wavelength_index[-1])] = 0

        # Perform trilinear interpolation to find emission values
        interpolation = RegularGridInterpolator( (self._airmass_index, self._water_vapor_index, self._wavelength_index), self._emission )
        interpolation = interpolation([[self.airmass.value, self.water_vapor.to(u.mm).value, λ] for λ in wavelengths_trim.to(u.angstrom).value])
        # Save interpolation values to results
        results[(self._wavelength_index[0] <= wavelengths) & (wavelengths <= self._wavelength_index[-1])] = interpolation
        return results * u.Unit('photon/(s arcsec^2 nm m^2)')

    
    def set_parameter(self, name, value):
        # TODO -- input validation
        if name == 'water_vapor' and not min(self._water_vapor_index) <= u.Quantity(value) <= max(self._water_vapor_index):
            raise ValueError(f'In atmosphere.set_parameter() -- water vapor {value} is not within bounds of [{min(self._water_vapor_index)}, {max(self._water_vapor_index)}]')
        
        if name == 'airmass' and not min(self._airmass_index) <= u.Quantity(value) <= max(self._airmass_index):
            raise ValueError(f'In atmosphere.set_parameter() -- water vapor {value} is not within bounds of [{min(self._airmass_index)}, {max(self._airmass_index)}]')
        
        if name == 'seeing' and u.Quantity(value).value <= 0:
            raise ValueError(f'In atmosphere.set_parameter() -- seeing {value} is invalid')

        vars(self)[name] = u.Quantity(value)