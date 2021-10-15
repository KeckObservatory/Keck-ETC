from astropy import units as u
from astropy.table import Table
import yaml
from os import listdir
import numpy as np
from scipy.interpolate import RegularGridInterpolator



class atmosphere:

    global _CONFIG_FILEPATH; _CONFIG_FILEPATH = 'sky_background/atmosphere_config.yaml'

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
        self.water_vapor_index = [u.Quantity(x).to(u.mm).value for x in self.config.water_vapor_index] * u.mm
        self.airmass_index = u.Quantity(self.config.airmass_index)
        self.config.wavelength_index = [u.Quantity(x).to(u.angstrom) for x in self.config.wavelength_index]
        self.wavelength_index = np.arange(
            u.Quantity(self.config.wavelength_index[0]).value,
            u.Quantity(self.config.wavelength_index[1]).value,
            u.Quantity(self.config.wavelength_index[2]).value
        ) * u.angstrom  # np.arange doesn't support units, see https://github.com/astropy/astropy/issues/11582
        self.transmission = np.zeros([len(self.airmass_index), len(self.water_vapor_index), len(self.wavelength_index)])
        self.emission = np.zeros([len(self.airmass_index), len(self.water_vapor_index), len(self.wavelength_index)])
        # Iterate through directory, filling in self.transmission and self.emission arrays
        for i, filename in enumerate(listdir(self.config.file_directory)):
            print('\rATMOSPHERE: Reading file '+str(i+1)+'/'+str(len(listdir(self.config.file_directory))), end='')
            try:
                if filename.startswith(self.config.transmission_filepath):
                    data = Table.read(self.config.file_directory+'/'+filename, format='ascii.ecsv')
                    self.transmission[
                        [x == u.Quantity(data.meta['airmass']) for x in self.airmass_index], 
                        [x == u.Quantity(data.meta['water_vapor']) for x in self.water_vapor_index],
                        :
                    ] = data['transmission'].to('')
                if filename.startswith(self.config.emission_filepath):
                    data = Table.read(self.config.file_directory+'/'+filename, format='ascii.ecsv')
                    self.emission[
                        [x == u.Quantity(data.meta['airmass']) for x in self.airmass_index], 
                        [x == u.Quantity(data.meta['water_vapor']) for x in self.water_vapor_index], 
                        :
                    ] = data['flux'].to('photon/(s arcsec^2 nm m^2)')
            except ValueError:
                raise ValueError('ERROR: In atmosphere._load_files() -- invalid file contents')
        print()  # newline for console output


    def _validate_config(self):
        # Throw errors if config file doesn't conform to requirements
        print('ATMOSPHERE: Validating configuration file',_CONFIG_FILEPATH)

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
            if not all([u.Quantity(Table.read(self.config.file_directory+'/'+x, format='ascii.ecsv', data_end=10).meta['water_vapor']) in test_wvi for x in test_em]):
                raise ValueError('ERROR: In atmosphere_config.yaml -- File matching emission_filepath has water_vapor that does not match water_vapor_index')
            if not all([u.Quantity(Table.read(self.config.file_directory+'/'+x, format='ascii.ecsv', data_end=10).meta['airmass']) in test_ami for x in test_em]):
                raise ValueError('ERROR: In atmosphere_config.yaml -- File matching emission_filepath has airmass that does not match airmass_index')
        except:
            raise ValueError('ERROR: In atmosphere_config.yaml -- File matching emission_filepath does not have a valid ECSV file header, check metadata')

        # Check transmission_filepath and transmission files
        test_tr = [x for x in listdir(self.config.file_directory) if x.startswith(self.config.transmission_filepath)]
        if not test_tr:
            raise ValueError('ERROR: In atmosphere_config.yaml -- file_directory or transmission_filepath is invalid, no matching files')
        try:
            if not all([u.Quantity(Table.read(self.config.file_directory+'/'+x, format='ascii.ecsv', data_end=10).meta['water_vapor']) in test_wvi for x in test_tr]):
                raise ValueError('ERROR: In atmosphere_config.yaml -- File matching transmission_filepath has water_vapor that does not match water_vapor_index')
            if not all([u.Quantity(Table.read(self.config.file_directory+'/'+x, format='ascii.ecsv', data_end=10).meta['airmass']) in test_ami for x in test_tr]):
                raise ValueError('ERROR: In atmosphere_config.yaml -- File matching transmission_filepath has airmass that does not match airmass_index')
        except:
            raise ValueError('ERROR: In atmosphere_config.yaml -- File matching transmission_filepath does not have a valid ECSV file header, check metadata')

        


    def __init__(self):
        self._mount_config(_CONFIG_FILEPATH)

        self._validate_config()

        self.seeing = [ u.Quantity(self.config.defaults.seeing) ]

        self.airmass = u.Quantity(self.config.defaults.airmass)

        self.water_vapor = u.Quantity(self.config.defaults.water_vapor)

        self._load_files()


    def _trilinear_interpolation(self, values, wavelengths):
        # Manual method, slower than RegularGridInterpolator, currently unused and probably will be deleted soon
        values = np.array([[np.interp(wavelengths, self.wavelength_index, x) for x in y] for y in values])
        am = [ self.airmass_index[self.airmass_index < self.airmass][-1].value, self.airmass_index[self.airmass_index > self.airmass][0].value ]
        wv = [ self.water_vapor_index[self.water_vapor_index < self.water_vapor][-1].value, self.water_vapor_index[self.water_vapor_index > self.water_vapor][0].value ]
        result = (1 / ( np.diff(am)*np.diff(wv) ))[0]
        result *= np.array([ [am[1]*wv[1], -am[1]*wv[0], -am[0]*wv[1], am[0]*wv[0]],
            [-wv[1], wv[0], wv[1], -wv[0]],
            [-am[1], am[1], am[0], -am[0]],
            [1, -1, -1, 1] ])
        result = np.matmul(result, [values[self.airmass_index.value==am[0], self.water_vapor_index.value==wv[0], :][0],
            values[self.airmass_index.value==am[0], self.water_vapor_index.value==wv[1], :][0],
            values[self.airmass_index.value==am[1], self.water_vapor_index.value==wv[0], :][0],
            values[self.airmass_index.value==am[1], self.water_vapor_index.value==wv[1], :][0]])
        result = np.matmul([1, self.airmass.value, self.water_vapor.value, self.airmass.value*self.water_vapor.value], result)
        #return np.interp(wavelengths, self.wavelength_index, result)
        return result


    def get_transmission(self, wavelengths):  # TODO -- replace out-of-bounds wavelengths with np.NaN instead of discarding

        # Check for and remove out-of-bounds wavelengths to avoid RegularGridInterpolator throwing errors
        wavelengths_trim = wavelengths[(self.wavelength_index[0] <= wavelengths) & (wavelengths <= self.wavelength_index[-1])]
        if len(wavelengths_trim) != len(wavelengths):
            print('WARNING: In atmosphere.get_transmission() -- some or all provided wavelengths are outside the current bounds of [' +
            str(self.wavelength_index[0])+', '+str(self.wavelength_index[-1])+'], discarding invalid values')

        # Perform trilinear interpolation to find transmission values
        interpolation = RegularGridInterpolator( (self.airmass_index, self.water_vapor_index, self.wavelength_index), self.transmission )
        return interpolation([[self.airmass.value, self.water_vapor.value, λ] for λ in wavelengths_trim.to(u.angstrom).value]) * u.Unit('')


    def get_emission(self, wavelengths):  # TODO -- replace out-of-bounds wavelengths with np.NaN instead of discarding
        # Check for and remove out-of-bounds wavelengths to avoid RegularGridInterpolator throwing errors
        wavelengths_trim = wavelengths[(self.wavelength_index[0] <= wavelengths) & (wavelengths <= self.wavelength_index[-1])]
        if len(wavelengths_trim) != len(wavelengths):
            print('WARNING: In atmosphere.get_emission() -- some or all provided wavelengths are outside the current bounds of [' +
            str(self.wavelength_index[0])+', '+str(self.wavelength_index[-1])+'], discarding invalid values')

        # Perform trilinear interpolation to find emission values
        interpolation = RegularGridInterpolator( (self.airmass_index, self.water_vapor_index, self.wavelength_index), self.emission )
        return interpolation([[self.airmass.value, self.water_vapor.value, λ] for λ in wavelengths_trim.to(u.angstrom).value]) * u.Unit('photon/(s arcsec^2 nm m^2)')