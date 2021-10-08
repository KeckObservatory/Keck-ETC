import yaml
from astropy.table import Table
import astropy.units as u
from numpy import interp, NaN, isnan

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
        filepath = '/usr/local/home/kblair/Documents/ETC/prototype/instruments/'+self.name+'/'+self.config.throughput_path
        self._throughput = Table.read(filepath, format='ascii.ecsv')



    def __init__(self, name):
        self.set_name(name)
        self.__dict__.update(vars(self.config.defaults))
        self._read_throughput()
        


    def get_throughput(self, wavelengths):
        data = self._throughput  # self._throughput[(self.grating, self.filter)] for deimos!!
        wav = data['wav']
        eff = data['eff']
        throughput = interp(wavelengths, wav, eff, left=NaN, right=NaN)
        if isnan(throughput).any():
            print('WARNING: In instrument.get_throughput() -- ' +
            'some or all provided wavelengths are outside the current bounds of ['+str(min(wav))+', '+str(max(wav))+'] '+str(wav.unit)+', returning NaN')
        return throughput

    def get_dark_current(self):
        # should this be dependent on wavelength??
        return u.Quantity(self.dark_current)

    def get_read_noise(self):
        return u.Quantity(self.read_noise)

    def set_name(self, name):
        config_filepath = '/usr/local/home/kblair/Documents/ETC/prototype/instruments/'+name+'/instrument_config.yaml'
        self._mount_config(config_filepath)
        self.name = name