import yaml
from astropy.table import Table
import astropy.units as u
from scipy.interpolate import interp1d as interpolate

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
        
    
    def _read_throughput(self):
        self._throughput = {}
        for g in self.config.gratings:
            for f in self.config.filters:
                filepath = '/usr/local/home/kblair/Documents/ETC/prototype/instruments/'+self.name+'/'+f+'_'+g+'.txt'
                data = Table.read(filepath, format='ascii.ecsv')
                self._throughput[(g, f)] = data


    def __init__(self, name):
        self.set_name(name)
        self.__dict__.update(vars(self.config.defaults))
        self._read_throughput()
        


    def get_throughput(self, wavelengths):
        # TODO: incorporate astropy for unit matching
        data = self._throughput[(self.grating, self.filter)]
        wav = data['wav']
        eff = data['eff']
        f = interpolate(wav, eff)
        try:
            throughput = f(wavelengths)
        except ValueError:
            print('WARNING: In instrument.get_throughput()\n'+
                '-- some or all provided wavelengths are outside the grating/filter bounds of ['+str(min(wav))+', '+str(max(wav))+'] -- returning only in-bound results')
            wavelengths = [x for x in wavelengths if min(wav) <= x <= max(wav)]
            return f(wavelengths)
        return throughput

    def get_dark_current(self):
        # should this be dependent on wavelength??
        return u.Quantity(vars(vars(self.config.dark_current)[self.mode])[self.amplifier])

    def get_read_noise(self):
        return u.Quantity(vars(vars(self.config.read_noise)[self.mode])[self.amplifier])

    def set_name(self, name):
        config_filepath = '/usr/local/home/kblair/Documents/ETC/prototype/instruments/'+name+'/instrument_config.yaml'
        self._mount_config(config_filepath)
        self.name = name