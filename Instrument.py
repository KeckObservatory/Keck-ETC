import yaml

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
        self.__dict__.update({'config': config})
        

    def __init__(self, name):
        config_filepath = '/usr/local/home/kblair/Documents/ETC/prototype/instruments/'+name+'/instrument_config.yaml'
        self._mount_config(config_filepath)


    def get_throughput(self, wavelengths):
        # Content comes later
        return []

    def get_dark_current(self, wavelengths):
        # TODO
        return []

    def get_read_noise(self, wavelengths):
        return []