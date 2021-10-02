from astropy import units as u
import yaml

class atmosphere:

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
        
    def _parse_unit_string(x):
        # If value isn't a string, treat it as a dimensionless unit --TODO: error handling if it's not a number
        if not isinstance(x, str):
            return x * u.dimensionless_unscaled
        
        # Otherwise, split the string along whitespace and parse quantity & unit with astropy --TODO: error handling for bad format strings
        return u.Quantity(x.split(' ')[0], unit=x.split(' ')[-1])


    def __init__(self):
        # Set default values based on config file
        config_filepath = '/usr/local/home/kblair/Documents/ETC/prototype/sky_background/atmosphere_config.yaml'
        self._mount_config(config_filepath)

        self.seeing = [ atmosphere._parse_unit_string(self.config.defaults.seeing) ]

        self.airmass = atmosphere._parse_unit_string(self.config.defaults.airmass)

        self.water_vapor = atmosphere._parse_unit_string(self.config.defaults.water_vapor)
    
    def setSeeing(self, seeing, unit):
        # Input validation here...

        self.seeing = seeing * unit

    def setAirmass(self, airmass, unit):
        # Input validation here...

        self.airmass = airmass * unit

    def setWaterVapor(self, water_vapor, unit):
        # Input validation here...

        self.water_vapor = water_vapor * unit

    def get_transmission(self, wavelengths):
        # TODO
        return []

    def get_emmission(self, wavelengths):
        # TODO
        return []