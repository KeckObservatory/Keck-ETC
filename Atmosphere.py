from astropy import units as u
from astropy.table import Table
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
        self.config = config


    def _load_files(self):
        # TODO
        test = Table.read('sky_background/mk_skybg_zm_10_10_ph.dat', format='ascii.ecsv')
        print(test)
        print(test['wavelength'][1])


    def __init__(self):
        # Set default values based on config file
        config_filepath = '/usr/local/home/kblair/Documents/ETC/prototype/sky_background/atmosphere_config.yaml'
        self._mount_config(config_filepath)

        self.seeing = [ u.Quantity(self.config.defaults.seeing) ]

        self.airmass = u.Quantity(self.config.defaults.airmass)

        self.water_vapor = u.Quantity(self.config.defaults.water_vapor)

        self._load_files()



    def get_transmission(self, wavelengths):
        # TODO
        return []

    def get_emmission(self, wavelengths):
        # TODO
        return []