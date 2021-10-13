from astropy import units as u
from astropy.table import Table
import yaml
from os import listdir
import numpy as np
from scipy.interpolate import RegularGridInterpolator



class atmosphere:

    global _config_filepath; _config_filepath = '/usr/local/home/kblair/Documents/ETC/prototype/sky_background/atmosphere_config.yaml'

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
        self.water_vapor_index = [u.Quantity(x).value for x in self.config.water_vapor_index] * u.Quantity(self.config.water_vapor_index[0]).unit
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
            print('\rAtmosphere: reading file '+str(i+1)+'/'+str(len(listdir(self.config.file_directory))), end='')
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
        print()  # newline for console output




    def __init__(self):
        # Set default values based on config file
        self._mount_config(_config_filepath)

        # TODO -- input validation here...
        #   - Check consistent units in water_vapor?

        self.seeing = [ u.Quantity(self.config.defaults.seeing) ]

        self.airmass = u.Quantity(self.config.defaults.airmass)

        self.water_vapor = u.Quantity(self.config.defaults.water_vapor)

        self._load_files()


    def _trilinear_interpolation(self, values, wavelengths):
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


    def get_transmission(self, wavelengths):
        # TODO -- error checking/handling, handle exterior grid points & out of bound wavelengths...
        interpolation = RegularGridInterpolator( (self.airmass_index, self.water_vapor_index, self.wavelength_index), self.transmission )
        try:
            return interpolation([[self.airmass.value, self.water_vapor.value, λ] for λ in wavelengths.to(u.angstrom).value]) * u.Unit('')
        except ValueError:
            print('ERROR in atmosphere.get_transmission(): requested wavelength out of bounds')
            return []


    def get_emission(self, wavelengths):
        # Check for airmass, water vapor values on grid points
        #if self.airmass in self.airmass_index:
        #    return []  # TODO
        #if self.water_vapor in self.water_vapor_index:
        #    return []  # TODO

        # Get airmass & vapor index values closest to current airmass & vapor
        emission = self._trilinear_interpolation(self.emission, wavelengths) * u.Unit('photon/(s arcsec^2 nm m^2)')

        return emission