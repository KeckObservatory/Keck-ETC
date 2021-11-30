import yaml
from astropy.table import Table
from io import BytesIO
from numpy import interp as interpolate
from numpy import NaN, isnan, exp, log, sqrt, pi, log10
from astropy.constants import c, h, k_B
import astropy.units as u
from base64 import b64decode
from warnings import warn


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
        self._functions = {}
        self.available_types = list(vars(self.config.source_types).keys())

        for name, source_type in vars(self.config.source_types).items():
            if 'filename' in vars(source_type).keys():
                data = Table.read(self.config.template_filepath+source_type.filename, format='ascii.ecsv')
                def define_data_scope(data):  # Wrapper function to narrow the scope of data and make sure each interpolation uses its own dataset
                    def scale_and_interpolate(w):  # TODO -- Figure out why each function is returning the same results...
                        wavelengths = data['wavelength'].to(u.angstrom) * (1 + self.redshift)  # Apply redshift
                        flux = data['flux'].to(u.photon / (u.cm**2 * u.s * u.angstrom), equivalencies=u.spectral_density(wavelengths) + self.spectral_density_vega(wavelengths.to(u.angstrom)))  # Convert to units of flux
                        central_wavelength = u.Quantity(vars(self.config.wavelength_bands)[self.wavelength_band])  # Get central wavelength of passband
                        flux = flux / interpolate(central_wavelength, wavelengths, flux) * self.brightness.to(u.photon / (u.cm**2 * u.s * u.angstrom), equivalencies=u.spectral_density(central_wavelength) + self.spectral_density_vega(central_wavelength.to(u.angstrom)))  # Scale source by given mag/flux
                        return interpolate(w, wavelengths, flux, left=0, right=0)
                    return scale_and_interpolate

                self._functions[name] = define_data_scope(data)  # Save function corresponding to this source
            else:
                if name == 'blackbody':
                    self._functions[name] = self._blackbody
                elif name == 'emission':
                    self._functions[name] = self._emission
                elif name == 'power':
                    self._functions[name] = self._power_law
                elif name == 'flat':
                    self._functions[name] = self._flat
                else:
                    raise ValueError('ERROR: In source_config.yaml -- source type '+name+' does not have either a defined template or function')
                if 'parameters' in vars(source_type).keys():
                    self.__dict__.update({key: u.Quantity(val) for key, val in vars(source_type.parameters).items()})


    def _validate_config(self):
        # Throw errors if config file doesn't conform to requirements
        try:
            # Check that all required fields exist and are spelled correctly
            _ = self.config.defaults.type
            # TODO -- validation for self.config.defaults.brightness here, needs extra because u.Quantity() errors out
            _ = u.Quantity(self.config.defaults.redshift)
            # TODO -- validate wavelength_bands and default.wavelength_band
        except:
            raise ValueError('ERROR: In source_config.yaml -- invalid configuration file')  # TODO -- specific error msg
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


    def _define_vegamag(self):
        self.vegamag = u.def_unit('mag(vega)', u.mag, format={'generic': 'mag(vega)', 'console': 'mag(vega)'})

        def define_data_scope(data):  # Wrapper function to narrow the scope of data and make sure each interpolation uses its own dataset
                    def shift_and_interpolate(w):  # TODO -- Figure out why each function is returning the same results...
                        wavelengths = data['wavelength'].to(u.angstrom) * (1 + self.redshift)  # Apply redshift
                        flux = data['flux'].to(u.photon / (u.cm**2 * u.s * u.angstrom), equivalencies=u.spectral_density(wavelengths) + self.spectral_density_vega(wavelengths.to(u.angstrom)))  # Convert to units of flux
                        return interpolate(w, wavelengths, flux, left=0, right=0)
                    return shift_and_interpolate
        
        self.vega_flux = define_data_scope(Table.read(self.config.template_filepath+'/'+self.config.vega_filename, format='ascii.ecsv'))

        # Define astropy equivalency
        def spectral_density_vega(w):

            photlam = u.photon/(u.cm**2 * u.s * u.angstrom)
            flam = u.erg/(u.cm**2 * u.s * u.angstrom)

            def converter_photlam(x):
                return -2.5 * log10(x / self.vega_flux(w).value)

            def iconverter_photlam(x):
                return self.vega_flux(w).value * 10**(-0.4*x)

            def converter_flam(x):
                return converter_photlam((x*flam).to(photlam, equivalencies=u.spectral_density(w)).value)

            def iconverter_flam(x):
                return (iconverter_photlam(x)*photlam).to(flam, equivalencies=u.spectral_density(w)).value

            def converter_jy(x):
                return converter_photlam((x*u.Jy).to(photlam, equivalencies=u.spectral_density(w)).value)

            def iconverter_jy(x):
                return (iconverter_photlam(x)*photlam).to(u.Jy, equivalencies=u.spectral_density(w)).value

            def converter_ab(x):
                return converter_photlam(u.Quantity(x, u.AB).to(photlam, equivalencies=u.spectral_density(w)).value)

            def iconverter_ab(x):
                return (iconverter_photlam(x)*photlam).to(u.AB, equivalencies=u.spectral_density(w)).value

            def converter_st(x):
                return converter_photlam(u.Quantity(x, u.ST).to(photlam, equivalencies=u.spectral_density(w)).value)

            def iconverter_st(x):
                return u.Quantity(iconverter_photlam(x), photlam).to(u.ST, equivalencies=u.spectral_density(w)).value


            return [
                    (photlam, self.vegamag, converter_photlam, iconverter_photlam),
                    (flam, self.vegamag, converter_flam, iconverter_flam),
                    (u.AB, self.vegamag, converter_ab, iconverter_ab),
                    (u.Jy, self.vegamag, converter_jy, iconverter_jy),
                    (u.ST, self.vegamag, converter_st, iconverter_st),
                ]

        self.spectral_density_vega = spectral_density_vega


    def set_type(self, new_type):
        if new_type not in self.available_types:
            warn(f'In Source.set_type() -- source type "{new_type}"" is not available', RuntimeWarning)
            return
        self.type = new_type
        self.active_parameters = list(vars(self.config.defaults).keys())
        if self.type in vars(self.config.source_types).keys() and 'parameters' in vars(vars(self.config.source_types)[self.type]).keys():
            self.__dict__.update({key: u.Quantity(val) for key, val in vars(vars(self.config.source_types)[self.type].parameters).items()})
            self.active_parameters += list(vars(vars(self.config.source_types)[self.type].parameters).keys())
        if self.type == 'blackbody':
            # Blackbody functions solely off of temperature!
            self.active_parameters.remove('brightness')
            self.active_parameters.remove('wavelength_band')


    def __init__(self):

        self._mount_config(_CONFIG_FILEPATH)

        self._validate_config()

        self.type = self.config.defaults.type
        self.set_brightness(self.config.defaults.brightness)
        self.redshift = u.Quantity(self.config.defaults.redshift)
        self.wavelength_band = self.config.defaults.wavelength_band

        self._load_files()

        self._define_vegamag()

        self.set_type(self.type)


    def _emission(self, wavelengths):
        # TODO -- Is there any reason to keep self.wavelength and self.wavelength_band separate? Can we ditch self.wavelength?
        # TODO -- Replace area / sqrt(2pi) σ w/ amplitude (brightness, unless we're keeping central wavelength and mag. band separate)
        central_wavelength = u.Quantity(vars(self.config.wavelength_bands)[self.wavelength_band])
        sigma = self.width / (2 * sqrt(2 * log(2) ))
        flux = self.brightness.to(u.photon / (u.cm**3 * u.s), equivalencies=u.spectral_density(wavelengths.to(u.angstrom)) + self.spectral_density_vega(wavelengths.to(u.angstrom))) / exp( (wavelengths - central_wavelength)**2/(2*sigma**2) )
        return flux


    def _blackbody(self, wavelengths):
        # TODO -- Ask Sherry about whether users should specify temp, mag, or give the option of either?
        # From https://pysynphot.readthedocs.io/en/latest/spectrum.html
        flux = (2*h*c**2 / wavelengths**5) / (exp(h*c/(wavelengths*self.temperature*k_B)) - 1) #/ u.steradian
        # Multiply by proper angle in order to remove the per steradian, hooowww?? Check with Sherry, easiest just to scale to given mag/flux, but is that what users will assume?

        return flux.to(u.photon / (u.cm**3 * u.s), equivalencies=u.spectral_density(wavelengths.to(u.angstrom)) + self.spectral_density_vega(wavelengths.to(u.angstrom)))


    def _flat(self, wavelengths):
        return ([self.brightness] * len(wavelengths) * self.brightness.unit).to(u.photon / (u.cm**3 * u.s), equivalencies=u.spectral_density(wavelengths.to(u.angstrom)) + self.spectral_density_vega(wavelengths.to(u.angstrom)))


    def _power_law(self, wavelengths):
        central_wavelength = u.Quantity(vars(self.config.wavelength_bands)[self.wavelength_band])
        flux = self.brightness.to(u.photon / (u.cm**3 * u.s), equivalencies=u.spectral_density(wavelengths.to(u.angstrom)) + self.spectral_density_vega(wavelengths.to(u.angstrom))) * (wavelengths / central_wavelength) ** self.index
        return flux

    
    def get_flux(self, wavelengths):
        flux = self._functions[self.type](wavelengths)
        # Check below is currently unecessary, I changed boundary handling to 0 instead of NaN -- but check w/ Sherry before deleting
        if isnan(flux).any():
            warn('In source.get_flux() -- some or all provided wavelengths are outside the current bounds, returning NaN', RuntimeWarning)
        return flux.to(u.photon / (u.cm**2 * u.s * u.angstrom), equivalencies=u.spectral_density(wavelengths.to(u.angstrom)) + self.spectral_density_vega(wavelengths.to(u.angstrom)))

    def add_template(self, template, name):
        # TODO -- input validation
        if name.lower().endswith('.txt'):
            template_string = b64decode(template).decode('utf-8').split('\n')
            data = Table.read(template_string, format='ascii.ecsv')
            for column in data.keys():
                data.rename_column(column, column.upper())
        elif name.lower().endswith('.fits'):
            template_binary = b64decode(template)
            data = Table.read(BytesIO(template_binary), format='fits')
        else:
            raise ValueError('In source.add_template() -- Provided file must be either FITS or ASCII.ECSV format')
        def define_data_scope(data):  # Wrapper function to narrow the scope of data and make sure each interpolation uses its own dataset
            def scale_and_interpolate(w):
                wavelengths = data['WAVELENGTH'].to(u.angstrom) * (1 + self.redshift)  # Apply redshift
                flux = data['FLUX'].to(u.photon / (u.cm**2 * u.s * u.angstrom), equivalencies=u.spectral_density(wavelengths) + self.spectral_density_vega(wavelengths.to(u.angstrom)))  # Convert to units of flux
                central_wavelength = u.Quantity(vars(self.config.wavelength_bands)[self.wavelength_band])  # Get central wavelength of passband
                flux = flux / interpolate(central_wavelength, wavelengths, flux) * self.brightness.to(u.photon / (u.cm**2 * u.s * u.angstrom), equivalencies=u.spectral_density(central_wavelength) + self.spectral_density_vega(central_wavelength.to(u.angstrom)))  # Scale source by given mag/flux
                return interpolate(w, wavelengths, flux, left=0, right=0)
            return scale_and_interpolate

        self._functions[name.split('.')[0]] = define_data_scope(data)  # Save function corresponding to this source
        self.available_types.append(name.split('.')[0])  # Add to list of types available to choose from
        # Add name to config so that it's accessible
        class GenericObject:
            pass
        obj = GenericObject()
        obj.name = name.split('.')[0]
        vars(self.config.source_types)[name.split('.')[0]] = obj

    def set_brightness(self, brightness):
        if isinstance(brightness, u.Quantity):
            self.brightness = brightness
        elif isinstance(brightness, str):
            conversion = [float(brightness.lower().replace(abmag,'')) * u.ABmag for abmag in ['magab', 'abmag', 'mag(ab)'] if brightness.lower().endswith(abmag)]
            if len(conversion) == 0:
                conversion = [float(brightness.lower().replace(stmag,'')) * u.STmag for stmag in ['magst', 'stmag', 'mag(st)'] if brightness.lower().endswith(stmag)]
            if len(conversion) == 0:
                conversion = [float(brightness.lower().replace(m_bol,'')) * u.m_bol for m_bol in ['magbol', 'bolmag', 'mag(bol)'] if brightness.lower().endswith(m_bol)]
            if len(conversion) == 0:
                conversion = [float(brightness.lower().replace(vega,'')) * self.vegamag for vega in ['magvega', 'vegamag', 'mag(vega)'] if brightness.lower().endswith(vega)]
            if len(conversion) == 0:
                self.brightness = u.Quantity(brightness)
            else:
                self.brightness = conversion[0]
        else:
            raise ValueError('ERROR: In source.set_brightness -- Brightness is not an astropy quantity or string')