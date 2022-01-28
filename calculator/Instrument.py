# Copyright (c) 2022, W. M. Keck Observatory
# All rights reserved.

# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. 


import yaml
from astropy.table import Table
import astropy.units as u
from numpy import interp, NaN, isnan
from warnings import warn
from re import split
from os import listdir

class instrument:

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
            class GenericObject:
                pass
            obj = GenericObject()
            # Loop over dictionary items and add to object
            for x in d:
                obj.__dict__[x] = _dict2obj(d[x])
            return obj
        # Open config file, convert & mount to self
        config = yaml.safe_load(open(config_path))
        config = _dict2obj(config)
        self.config = config
        

    def _update_wavelengths(self):
        self.min_wavelength = self._current_throughput()['WAV'][0] * self._current_throughput()['WAV'].unit
        self.max_wavelength = self._current_throughput()['WAV'][-1] * self._current_throughput()['WAV'].unit


    def _current_throughput(self):
        # Gather applicable parameters for proper throughput file
        parameters = {}
        if 'mode' in vars(self).keys():
            parameters['MODE'] = self.mode
        if 'filter' in vars(self).keys():
            parameters['FILTER'] = self.filter
        if 'grating' in vars(self).keys():
            parameters['GRATING'] = self.grating
        if 'grism' in vars(self).keys():
            parameters['GRISM'] = self.grism
        if 'dichroic' in vars(self).keys():
            parameters['DICHROIC'] = self.dichroic
        # Select throughput file matching instrument parameters
        result = None
        for throughput in self._throughput:
            if all([ throughput.meta[key] == val for key, val in parameters.items() ]):
                result = throughput
        # If no throughput files matched, instrument mode/grating/filter/grism combination is invalid
        if result is None:
            raise ValueError('In instrument.get_throughput() -- instrument mode/grating/filter/grism combination is invalid')
        
        return result


    def _read_throughput(self):
        self._throughput = []
        directory = 'calculator/instruments/'+self.name+'/'+self.config.throughput_path
        for filename in listdir(directory):
            data = Table.read(directory + '/' + filename, format='fits')
            data['EFF'].unit = u.electron / u.photon
            self._throughput.append(data)


    def __init__(self, name):
        self.set_name(name)
        
        


    def get_throughput(self, wavelengths):
        data = self._current_throughput()
        throughput = interp(wavelengths, data['WAV'], data['EFF'], left=NaN, right=NaN)
        if isnan(throughput).any():
            warn('In instrument.get_throughput() -- ' +
            'some or all provided wavelengths are outside the current bounds of ['+str(min(data['WAV']))+', '+str(max(data['WAV']))+'] '+str(data['WAV'].unit)+', returning NaN', RuntimeWarning)
        return u.Quantity(throughput, data['EFF'].unit)

    def get_dark_current(self):
        return self._dark_current

    def get_read_noise(self):
        return self._read_noise

    def set_mode(self, mode):
        self.mode = mode
        config = vars(self.config)[self.mode]
        self.gain = u.Quantity(config.gain)
        self.pixel_size = u.Quantity(config.pixel_size)
        self._dark_current = u.Quantity(config.dark_current)
        self._read_noise = u.Quantity(config.read_noise)
        self.spectral_resolution = u.Quantity(config.spectral_resolution)
        self.nonlinear_depth = u.Quantity(config.nonlinear_depth)
        self.slit_options = [ [u.Quantity(x) for x in y] * u.arcsec for y in config.slit_options] * u.arcsec

    def set_name(self, name):
        self.__dict__ = {}  # clear parameters from previous instrument
        config_filepath = 'calculator/instruments/'+name+'/instrument_config.yaml'
        self._mount_config(config_filepath)
        self.name = name
        
        self.slit = [u.Quantity(x) for x in self.config.defaults.slit] * u.arcsec
        self.active_parameters = ['name', 'slit', 'mode', 'binning']
        for parameter in ['grating', 'grism', 'filter', 'dichroic']:
            if parameter in vars(self.config.defaults).keys():
                vars(self)[parameter] = vars(self.config.defaults)[parameter]
                self.active_parameters.append(parameter)
        # More explicit aliases for slit
        self.slit_width = self.slit[0]
        self.slit_length = self.slit[1]
        self.binning = u.Quantity(self.config.defaults.binning)

        self.set_mode(self.config.defaults.mode)
        
        self._read_throughput()
        self._update_wavelengths()

    def set_parameter(self, name, value):
        # TODO -- input validation
        if name == 'name':
            self.set_name(value.lower())
        elif name == 'mode':
            if value not in self.config.mode_options:
                raise ValueError(f'In instrument.set_parameter() -- "{value}" is not a valid mode')
            self.set_mode(str(value).lower())
            self._update_wavelengths()
        elif name == 'grating':
            if value not in vars(self.config)[self.mode].grating_options:
                raise ValueError(f'In instrument.set_parameter() -- "{value}" is not a valid grating')
            self.grating = str(value).upper()
            self._update_wavelengths()
        elif name == 'filter':
            if value not in vars(self.config)[self.mode].filter_options:
                raise ValueError(f'In instrument.set_parameter() -- "{value}" is not a valid filter')
            self.filter = str(value).upper()
            self._update_wavelengths()
        elif name == 'grism':
            if value not in vars(self.config)[self.mode].grism_options:
                raise ValueError(f'In instrument.set_parameter() -- "{value}" is not a valid grism')
            self.grism = str(value).upper()
            self._update_wavelengths()
        elif name == 'dichroic':
            if value not in vars(self.config)[self.mode].dichroic_options:
                raise ValueError(f'In instrument.set_parameter() -- "{value}" is not a valid dichroic')
            self.dichroic = str(value).upper()
            self._update_wavelengths()
        elif name == 'binning':
            if isinstance(value, str):
                value = [int(x) for x in split('x|,', value)]
            elif isinstance(value, list):
                value = [int(x) for x in value]
            if value not in vars(self.config)[self.mode].binning_options or not isinstance(value, list):
                raise ValueError(f'In instrument.set_parameter() -- "{value}" is not a valid binning value')
            self.binning = u.Quantity(value)
        elif name == 'slit':
            # If value is "custom", reset to default
            if str(value).lower() == 'custom':
                self.slit = [u.Quantity(x) for x in self.config.defaults.slit] * u.arcsec
                self.slit_width = self.slit[0]
                self.slit_length = self.slit[1]
            else:
                if isinstance(value, str):
                    # Allow formats of width x height or width,height
                    value = split('x|,', value)
                try:
                    # If dimensionless, assume arcsec
                    value = [u.Quantity(x) * u.arcsec if u.Quantity(x).unit==u.dimensionless_unscaled else u.Quantity(x) for x in value] * u.arcsec
                    if (not vars(self.config)[self.mode].custom_slits) and (not any([(value==x).all() for x in self.slit_options])):
                        raise ValueError()
                    self.slit = value
                    self.slit_width = self.slit[0]
                    self.slit_length = self.slit[1]
                except Exception:
                    raise ValueError(f'In instrument.set_parameter() -- "{value}" is not a valid slit value')
        elif name == 'slit_width' or name == 'slit_length':
            raise ValueError('In instrument.set_parameter() -- must use set_parameter("slit", [width,length]) to set slit width or length')
        else:
            vars(self)[name] = u.Quantity(value)