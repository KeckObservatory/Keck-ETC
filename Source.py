import yaml
from astropy.table import Table
from numpy import interp as interpolate
from numpy import NaN, isnan, exp
from astropy.constants import c, h, k_B


class source:

    global _CONFIG_FILEPATH; _CONFIG_FILEPATH = 'source/source_config.yaml'

    def _mount_config(self, config_path):
        # From https://www.geeksforgeeks.org/convert-nested-python-dictionary-to-object/
        def _dict2obj(d):
            # If list, recursively unpack
            if isinstance(d, list):
                d = [_dict2obj(x) for x in d]
            # If not list or dictionary, return object
            if not isinstance(d, dict):
                return d

            # Otherwise, create generic object
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


    def _load_files(self):
        self.functions = {}
        for name, source in vars(self.config.source_types):
            if source.filename.lower() != 'none':
                data = Table.read(self.config.template_filepath+source.filename)
                # Figure out how to scale flux by the magnitude -- and units, see https://docs.astropy.org/en/stable/units/equivalencies.html for conversions!
                self.functions[name] = lambda w: interpolate(w, data['wavelength'] * (1 + self.redshift), data['flux'], left=NaN, right=NaN)

    def _validate_config(self):
        pass  # TODO


    def __init__(self):
        self._mount_config(_CONFIG_FILEPATH)

        self._validate_config()

        self.__dict__.update(vars(self.config.defaults))

        self._load_files()


    def _gaussian(self, wavelengths):
        pass  # TODO


    def _blackbody(self, wavelengths):
        # From https://pysynphot.readthedocs.io/en/latest/spectrum.html
        flux = (2*h*c / wavelengths**5) / (exp(h*c/(wavelengths*self.temperature*k_B)) - 1)
        return flux


    def _flat(self, wavelengths):
        pass  # TODO


    def _power(self, wavelengths):
        pass  # TODO

    
    def get_flux(self, wavelengths):
        filepath = self.config.template_filepath + vars(self.config.templates)[self.type]
        spectra = Table.read(filepath, format='ascii.ecsv')
        spectra['wavelength'] = spectra['wavelength'] * (1 + self.redshift)  # Apply redshift
        flux = interpolate(wavelengths, spectra['wavelength'], spectra['flux'], left=NaN, right=NaN)
        if isnan(flux).any():
            print('WARNING: In source.get_flux() -- some or all provided wavelengths are outside the current bounds of [' +
                    str(min(spectra['wavelength']))+', '+str(max(spectra['wavelength']))+'] '+str(spectra['wavelength'].unit)+', returning NaN')
        return flux

    def add_template(self, template, name):
        pass  # TODO -- allow users to specify their own source templates (i.e. upload file)