from astropy import units as u
from Instrument import instrument
from Source import source
from Atmosphere import atmosphere
import yaml

class run_etc:

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
        self.__dict__.update({'config': config})


    def _validate_config(self):
        pass  # TODO


    def _calculate(self):
        pass  # TODO


    def __init__(self):
        # Set default values based on config file
        config_filepath = '/usr/local/home/kblair/Documents/ETC/prototype/config.yaml'
        self._mount_config(config_filepath)
        self._validate_config()

        # Initialize objects
        self.instrument = instrument(self.config.defaults.instrument)
        self.atmosphere = atmosphere()
        self.source = source()

        # Initialize values
        self.exposure = u.Quantity(self.config.defaults.exposure)
        self.snr = u.Quantity(self.config.defaults.snr)
        self.dither = u.Quantity(self.config.defaults.dither)
        self.read = u.Quantity(self.config.defaults.read)
        self.repeat = u.Quantity(self.config.defaults.repeat)
        self.coadd = u.Quantity(self.config.defaults.coadd)

        self._calculate()