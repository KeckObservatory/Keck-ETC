import yaml
from astropy.table import Table
import astropy.units as u
from numpy import interp, NaN, isnan
from warnings import warn

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
        filepath = 'instruments/'+self.name+'/'+self.config.throughput_path
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
        config_filepath = 'instruments/'+name+'/instrument_config.yaml'
        self._mount_config(config_filepath)
        self.name = name

        self._validate_config()

        # Maybe move these, find the most appropriate place later...
        self.slit_width = u.Quantity(self.config.defaults.slit_width)
        self.slit_length = u.Quantity(self.config.defaults.slit_length)
        self.pixel_size = u.Quantity(self.config.defaults.pixel_size)
        self._dark_current = u.Quantity(self.config.dark_current)
        self._read_noise = u.Quantity(self.config.read_noise)
        self.spectral_resolution = u.Quantity(self.config.spectral_resolution)
        self.mode = self.config.defaults.mode  # Currently does nothing, TODO -- support for different modes


        self._read_throughput()