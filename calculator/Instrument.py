import yaml
from astropy.table import Table
import astropy.units as u
from numpy import interp, NaN, isnan
from warnings import warn
from re import split

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
            class DummyObject:
                pass
            obj = DummyObject()
            # Loop over dictionary items and add to object
            for x in d:
                obj.__dict__[x] = _dict2obj(d[x])
            return obj
        # Open config file, convert & mount to self
        config = yaml.safe_load(open(config_path))
        config = _dict2obj(config)
        self.config = config
        
    
    def _read_throughput(self):
        # Code for deimos, once I have multiple instruments, maybe include config option like "throughput_path_type: template ? file"...
        # self._throughput = {}
        # for g in self.config.gratings:
        #     for f in self.config.filters:
        #         filepath = '/usr/local/home/kblair/Documents/ETC/prototype/instruments/'+self.name+'/'+f+'_'+g+'.txt'
        #         data = Table.read(filepath, format='ascii.ecsv')
        #         self._throughput[(g, f)] = data
        filepath = 'calculator/instruments/'+self.name+'/'+self.config.throughput_path
        self._throughput = Table.read(filepath, format='ascii.ecsv')
        self.min_wavelength = self._throughput['wav'][0] * self._throughput['wav'].unit
        self.max_wavelength = self._throughput['wav'][-1] * self._throughput['wav'].unit


    def _validate_config(self):
        pass  # TODO

    def __init__(self, name):
        self.set_name(name)
        
        


    def get_throughput(self, wavelengths):
        data = self._throughput  # self._throughput[(self.grating, self.filter)] for deimos!!
        throughput = interp(wavelengths, data['wav'], data['eff'], left=NaN, right=NaN)
        if isnan(throughput).any():
            warn('In instrument.get_throughput() -- ' +
            'some or all provided wavelengths are outside the current bounds of ['+str(min(data['wav']))+', '+str(max(data['wav']))+'] '+str(data['wav'].unit)+', returning NaN', RuntimeWarning)
        return u.Quantity(throughput, data['eff'].unit)

    def get_dark_current(self):
        # should this be dependent on wavelength??
        return self._dark_current

    def get_read_noise(self):
        return self._read_noise

    def set_name(self, name):
        self.__dict__ = {}  # clear parameters from previous instrument
        config_filepath = 'calculator/instruments/'+name+'/instrument_config.yaml'
        self._mount_config(config_filepath)
        self.name = name

        self._validate_config()

        # Maybe move these, find the most appropriate place later...
        self.gain = u.Quantity(self.config.gain)
        self.slit = [u.Quantity(x) for x in self.config.defaults.slit] * u.arcsec
        # More explicit aliases for slit
        self.slit_width = self.slit[0]
        self.slit_length = self.slit[1]
        self.binning = u.Quantity(self.config.defaults.binning)
        self.pixel_size = u.Quantity(self.config.defaults.pixel_size)
        self._dark_current = u.Quantity(self.config.dark_current)
        self._read_noise = u.Quantity(self.config.read_noise)
        self.spectral_resolution = u.Quantity(self.config.spectral_resolution)
        self.nonlinear_depth = u.Quantity(self.config.nonlinear_depth)
        self.slit_options = [ [u.Quantity(x) for x in y] * u.arcsec for y in self.config.slit_options] * u.arcsec
        self.mode = self.config.defaults.mode  # Currently does nothing, TODO -- support for different modes
        self.active_parameters = ['name', 'slit', 'mode', 'binning']  # TODO -- adjust based on gratings, grism, filter, etc.
        

        self._read_throughput()

    def set_parameter(self, name, value):
        # TODO -- input validation
        if name == 'name':
            self.set_name(value)
        elif name == 'mode':
            self.mode = str(value)
        elif name == 'binning':
            if isinstance(value, str):
                value = [int(x) for x in split('x|,', value)]
            elif isinstance(value, list):
                value = [int(x) for x in value]
            if value not in self.config.binning_options or not isinstance(value, list):
                raise ValueError(f'In instrument.set_parameter() -- "{value}" is not a valid binning value')
            self.binning = u.Quantity(value)
        elif name == 'slit':
            if isinstance(value, str):
                value = split('x|,', value)
            try:
                # If dimensionless, assume arcsec, otherwise convert to arcsec
                value = [u.Quantity(x) * u.arcsec if u.Quantity(x).unit==u.dimensionless_unscaled else u.Quantity(x) for x in value] * u.arcsec
                if (not self.config.custom_slits) and (not any([(value==x).all() for x in self.slit_options])):
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