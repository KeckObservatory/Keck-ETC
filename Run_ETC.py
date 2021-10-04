from astropy import units as u
from Instrument import instrument
from Source import source
from Atmosphere import atmosphere

def _parse_unit_string(x):
    # If value isn't a string, treat it as a dimensionless unit --TODO: error handling if it's not a number
    if not isinstance(x, str):
        return x * u.dimensionless_unscaled
    
    # Otherwise, split the string along whitespace and parse quantity & unit with astropy --TODO: error handling for bad format strings
    return u.Quantity(x.split(' ')[0], unit=x.split(' ')[-1])

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


    def __init__(self):
        # Set default values based on config file
        config_filepath = '/usr/local/home/kblair/Documents/ETC/prototype/config.yaml'
        self._mount_config(config_filepath)

        # Initialize objects
        self.instrument = instrument(self.config.defaults.instrument)
        self.atmosphere = atmosphere()
        self.source = source()

        # Initialize values
        self.exposure = parse_unit_string(self.config.defaults.exposure)
        self.snr = parse_unit_string(self.config.defaults.snr)
        self.dither = parse_unit_string(self.config.defaults.dither)
        self.read = parse_unit_string(self.config.defaults.read)
        self.repeat = parse_unit_string(self.config.defaults.repeat)
        self.coadd = parse_unit_string(self.config.defaults.coadd)

        self._calculate()