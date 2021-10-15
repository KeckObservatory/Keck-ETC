import yaml
from astropy.table import Table
from numpy import interp as interpolate
from numpy import NaN, isnan, exp, log, sqrt, pi
from astropy.constants import c, h, k_B
import astropy.units as u


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

        for name, source_type in vars(self.config.source_types).items():
            if 'filename' in vars(source_type).keys():
                data = Table.read(self.config.template_filepath+source_type.filename, format='ascii.ecsv')
                # TODO -- Figure out how to scale flux by the magnitude!
                flux = data['flux'].to(u.photon / (u.cm**3 * u.s), equivalencies=u.spectral_density(data['wavelength'].to(u.angstrom)))
                self.functions[name] = lambda w: interpolate(w, data['wavelength'] * (1 + self.redshift), flux, left=NaN, right=NaN)
            else:
                if name == 'blackbody':
                    self.functions[name] = self._blackbody
                elif name == 'gaussian':
                    self.functions[name] = self._gaussian
                elif name == 'power':
                    self.functions[name] = self._power_law
                elif name == 'flat':
                    self.functions[name] = self._flat
                else:
                    raise ValueError('ERROR: In source_config.yaml -- source type '+name+' does not have either a defined template or function')
                if 'parameters' in vars(source_type).keys():
                    self.__dict__.update({key: u.Quantity(val) for key, val in vars(source_type.parameters).items()})


    def _validate_config(self):
        # Throw errors if config file doesn't conform to requirements
        print('SOURCE: Validating configuration file', _CONFIG_FILEPATH)
        try:
            # Check that all required fields exist and are spelled correctly
            _ = self.config.defaults.type
            _ = u.Quantity(self.config.defaults.brightness)
            _ = u.Quantity(self.config.defaults.redshift)
            # For each source type, check name (required), filename and parameters
            for source_type in vars(self.config.source_types).values():
                _ = source_type.name
                # Check for valid template filenames
                if 'filename' in vars(source_type).keys():
                    filepath = self.config.template_filepath + '/' + source_type.filename
                    try:
                        data = Table.read(filepath, format='ascii.ecsv', data_end=10)
                        _ = data['wavelength'].unit
                        _ = data['flux'].unit
                    except:
                        raise ValueError('ERROR: In source--config.yaml -- file '+filepath+' is not a valid ECSV file')
                # Check parameters for valid astropy quantities
                if 'parameters' in vars(source_type).keys():
                    try:
                        _ = [u.Quantity(z) for z in vars(source_type.parameters).values()]
                    except:
                        raise ValueError('ERROR: In source_config.yaml -- invalid parameter for source type '+source_type.name)
        except:
            raise ValueError('ERROR: In source_config.yaml -- invalid configuration file')


    def set_type(self, new_type):
        self.type = new_type
        self.active_parameters = list(vars(self.config.defaults).keys())
        if 'parameters' in vars(vars(self.config.source_types)[self.type]).keys():
            self.__dict__.update({key: u.Quantity(val) for key, val in vars(vars(self.config.source_types)[self.type].parameters).items()})
            self.active_parameters += list(vars(vars(self.config.source_types)[self.type].parameters).keys())


    def __init__(self):
        self._mount_config(_CONFIG_FILEPATH)

        self._validate_config()

        self.type = self.config.defaults.type
        self.brightness = u.Quantity(self.config.defaults.brightness)
        self.redshift = u.Quantity(self.config.defaults.redshift)

        self._load_files()

        print(vars(self))
        self.set_type(self.type)


    def _gaussian(self, wavelengths):
        sigma = self.fwhm / (2 * sqrt(2 * log(2) ))
        flux = self.brightness / (sqrt(2*pi) * sigma) / exp( (wavelengths - self.wavelength)**2/(2*sigma**2) )
        return flux.to(u.photon / (u.cm**3 * u.s), equivalencies=u.spectral_density(wavelengths.to(u.angstrom)))


    def _blackbody(self, wavelengths):
        # From https://pysynphot.readthedocs.io/en/latest/spectrum.html
        flux = (2*h*c**2 / wavelengths**5) / (exp(h*c/(wavelengths*self.temperature*k_B)) - 1)
        return flux.to(u.photon / (u.cm**3 * u.s), equivalencies=u.spectral_density(wavelengths.to(u.angstrom)))


    def _flat(self, wavelengths):
        return ([self.brightness.value] * len(wavelengths) * self.brightness.unit).to(u.photon / (u.cm**3 * u.s), equivalencies=u.spectral_density(wavelengths.to(u.angstrom)))


    def _power_law(self, wavelengths):
        # TODO -- figure out how to scale for given magnitude
        flux = self.brightness * (wavelengths / self.wavelength) ** self.index
        return flux.to(u.photon / (u.cm**3 * u.s), equivalencies=u.spectral_density(wavelengths.to(u.angstrom)))

    
    def get_flux(self, wavelengths):
        flux = self.functions[self.type](wavelengths)
        if isnan(flux).any():
            print('WARNING: In source.get_flux() -- some or all provided wavelengths are outside the current bounds, returning NaN')
        return flux

    def add_template(self, template, name):
        pass  # TODO -- allow users to specify their own source templates (i.e. upload file)
                # Need to figure out file formats w/ bokeh & api to know what I should require