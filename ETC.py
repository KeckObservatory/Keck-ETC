from astropy import units as u
from Instrument import instrument
from Source import source
from Atmosphere import atmosphere
import yaml
from numpy import pi, linspace, zeros, array, arccos, sqrt, NaN
from warnings import warn
from json import loads as json_loads

class exposure_time_calculator:

    global _CONFIG_FILEPATH; _CONFIG_FILEPATH = './config.yaml'

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

        slit_size = self.instrument.slit_width * self.instrument.slit_length
        slit_size_pixels = slit_size / self.instrument.pixel_size
        # Area of circular point source minus area of segments
        area_occluded = (self.atmosphere.seeing**2 * arccos(self.instrument.slit_width / self.atmosphere.seeing)/u.rad - self.instrument.slit_width * sqrt(self.atmosphere.seeing**2 - self.instrument.slit_width**2))/2 if self.atmosphere.seeing > self.instrument.slit_width else 0
        source_size = (pi * (self.atmosphere.seeing/2)**2) - area_occluded
        # Percentage of source inside slit
        source_slit_ratio = source_size / (pi * (self.atmosphere.seeing/2)**2)

        # Total number of subexposures, to be multiplied by exposure time
        number_exposures = self.dithers * self.repeats * self.coadds

        self.source_flux = self.source.get_flux(self.wavelengths) * self.atmosphere.get_transmission(self.wavelengths)

        source_rate = self.source_flux * self.instrument.get_throughput(self.wavelengths) * self.binning[0] * self.binning[1]  # Binning in the spectral direction
        source_rate *= self.telescope_area * source_slit_ratio * (self.wavelengths / self.instrument.spectral_resolution) * self.reads  


        background_rate = self.atmosphere.get_emission(self.wavelengths) * self.instrument.get_throughput(self.wavelengths) * self.binning[0] * self.binning[1]
        background_rate *= self.telescope_area * slit_size * (self.wavelengths / self.instrument.spectral_resolution) * self.reads
        # Divide reads by 2 because read noise is per CDS (2 reads)
        read_noise = self.instrument.get_read_noise()**2 * (self.reads/2) * slit_size_pixels / self.binning[0]  # Binning in the spatial direction

        dark_current_rate = self.instrument.get_dark_current() * slit_size_pixels
        
        if self.target == 'signal_noise_ratio':

            if len(self.exposure) == 0:
                self.exposure = [u.Quantity(x) for x in self.config.defaults.exposure] * u.s
                warn('In ETC -- exposure is not defined, defaulting to '+str(self.exposure), RuntimeWarning)

            # Compute and save counts in ADU/pixel
            self.source_count_adu = [source_rate * self.instrument.pixel_size / source_size * exp * number_exposures / self.instrument.gain for exp in self.exposure] * (u.adu/u.pixel)
            self.background_count_adu = [background_rate / slit_size * self.instrument.pixel_size * exp * number_exposures / self.instrument.gain for exp in self.exposure] * (u.adu/u.pixel)
            self.dark_current_count_adu = [dark_current_rate / slit_size_pixels * exp * number_exposures / self.instrument.gain for exp in self.exposure] * (u.adu/u.pixel)
            self.read_noise_count_adu = ([read_noise / slit_size_pixels * number_exposures / self.instrument.gain] * len(self.exposure)) * (u.adu/u.pixel)

            # Save total integration time
            self.total_exposure_time = [(number_exposures * exp) for exp in self.exposure] * u.s

            # Get counts in e- over entire slit during exposure
            source_count_e = [source_rate * exp * number_exposures for exp in self.exposure] * u.electron
            background_count_e = [background_rate * exp * number_exposures for exp in self.exposure] * u.electron
            dark_current_count_e = [dark_current_rate * exp * number_exposures for exp in self.exposure] * u.electron
            read_noise_count_e = ([read_noise * number_exposures] * len(self.exposure)) * u.electron
            
            # Sum counts to get total noise
            noise_count = [source_count_e[exp] + background_count_e[exp] + dark_current_count_e[exp] + read_noise_count_e[exp] for exp in range(len(self.exposure))]  # Total count in e- for whole slit and exposure
            
            # Signal to noise ratio = signal / sqrt(noise)
            self.signal_noise_ratio = [(source_count_e[exp] * noise_count[exp] ** (-1/2)).value for exp in range(len(self.exposure))] * u.dimensionless_unscaled # Remove the sqrt(e-) unit because it's nonphysical

        elif self.target == 'exposure':

            if len(self.signal_noise_ratio) == 0:
                self.signal_noise_ratio = [u.Quantity(x) for x in self.config.defaults.signal_noise_ratio] * u.dimensionless_unscaled
                warn('In ETC -- signal_noise_ratio is not defined, defaulting to '+str(self.signal_noise_ratio), RuntimeWarning)

            # Initialize exposure array for output
            self.exposure = zeros([len(self.signal_noise_ratio), len(self.wavelengths)])

            for idx, snr in enumerate(self.signal_noise_ratio.value * u.electron**(1/2)):

                # Define a, b, c for quadratic formula
                # Adding 0j to avoid generating RuntimeWarning for sqrt(-1)
                a = self.dithers * source_rate**2 + 0j
                b = - snr**2 * (background_rate + dark_current_rate + source_rate) + 0j
                c = [(read_noise * snr**2).to(u.electron**2).value] * len(self.wavelengths) * u.electron**2 + 0j

                # Quadratic formula
                exposure = ( -b + (b**2 - 4*a*c)**(1/2) ) / (2 * a)
                #exposure_neg = ( -b - (b**2 - 4*a*c)**(1/2) ) / (2 * a)
                # This statement is broken, iter() needs to be moved outside because it reinitializes every time
                #exposure = [next(iter(exposure_pos)) if check else next(iter(exposure_neg)) for check in (exposure_pos.real >= 0) & (exposure_pos.imag == 0)] * u.s
                if ((exposure.real < 0) | (exposure.imag != 0)).any():
                    exposure[(exposure.real < 0) | (exposure.imag != 0)] = NaN
                    warn('In ETC -- Some/all solutions do not exist for S/N = '+str(snr.value)+', returning exposure = NaN', RuntimeWarning)
                self.exposure[idx, :] = exposure.real.to(u.s)

            self.exposure = u.Quantity(self.exposure, u.s)  # Convert ndarray to quantity

            # Calculate and save counts based on calculatred exposure = f(λ)
            # TODO -- convert to list of lists instead of list, this will break for multiple snr!!!
            self.source_count_adu = [source_rate * self.instrument.pixel_size / source_size * exp * number_exposures / self.instrument.gain for exp in self.exposure] * (u.adu/u.pixel)
            self.background_count_adu = [background_rate / slit_size * self.instrument.pixel_size * exp * number_exposures / self.instrument.gain for exp in self.exposure] * (u.adu/u.pixel)
            self.dark_current_count_adu = [dark_current_rate / slit_size_pixels * exp * number_exposures / self.instrument.gain for exp in self.exposure] * (u.adu/u.pixel)
            self.read_noise_count_adu = ([[(read_noise / slit_size_pixels * number_exposures / self.instrument.gain).to(u.adu/u.pixel).value] * len(self.wavelengths)] * len(self.exposure)) * (u.adu/u.pixel)
            # Save total integration time
            self.total_exposure_time = [(number_exposures * exp) for exp in self.exposure] * u.s


        else:
            # Check that exposure and S/N have not both been provided
            raise ValueError('ERROR: In ETC -- target must be set to "exposure" or "signal_noise_ratio"')


    def __init__(self):
        # Set default values based on config file
        self._mount_config(_CONFIG_FILEPATH)
        self._validate_config()

        # Initialize objects
        self.instrument = instrument(self.config.defaults.instrument)
        self.atmosphere = atmosphere()
        self.source = source()

        # Initialize values
        self.telescope_area = u.Quantity(self.config.telescope_area)
        self.exposure = [u.Quantity(x) for x in self.config.defaults.exposure] * u.s
        self.signal_noise_ratio = [u.Quantity(x) for x in self.config.defaults.signal_noise_ratio] * u.dimensionless_unscaled
        self.dithers = u.Quantity(self.config.defaults.dithers)
        self.reads = u.Quantity(self.config.defaults.reads)
        self.repeats = u.Quantity(self.config.defaults.repeats)
        self.coadds = u.Quantity(self.config.defaults.coadds)
        self.target = self.config.defaults.target
        self.binning = u.Quantity(self.config.defaults.binning)
        # Calculate default wavelengths array from min, max of instrument and atmosphere
        min_wavelength = max(self.atmosphere._wavelength_index[0], self.instrument.min_wavelength)
        max_wavelength = min(self.atmosphere._wavelength_index[-1], self.instrument.max_wavelength)
        self.wavelengths = linspace(min_wavelength, max_wavelength, self.config.defaults.default_wavelengths_number)

        self._calculate()

    def set_parameters(self, parameter_string):
        # TODO -- input validation
        parameters = json_loads(parameter_string)
        for key, val in parameters.items():
            self.set_parameter(key, val)


    def set_parameter(self, name, value):
        # TODO -- validation
        if name.startswith('instrument.'):
            self._set_instrument_parameter('.'.join(name.split('.')[1:]), value)
        elif name.startswith('source.'):
            self._set_source_parameter('.'.join(name.split('.')[1:]), value)
        elif name.startswith('atmosphere.'):
            self._set_atmosphere_parameter('.'.join(name.split('.')[1:]), value)
        else:
            if name == 'target':
                if value != 'signal_noise_ratio' or value != 'exposure':
                    raise ValueError('In ETC.set_parameter() -- target must be either "exposure" or "signal_noise_ratio"')
                if value == 'exposure' and self.target == 'signal_noise_ratio':
                    self.signal_noise_ratio = [u.Quantity(x) for x in self.config.defaults.signal_noise_ratio] * u.dimensionless_unscaled
                elif value == 'signal_noise_ratio' and self.target == 'exposure':
                    self.exposure = [u.Quantity(x) for x in self.config.defaults.exposure] * u.s
                self.target = value
            if name == 'exposure':
                self.target = 'signal_noise_ratio'
                self.exposure = [u.Quantity(x).to(u.s) for x in value] * u.s
            elif name == 'signal_noise_ratio':
                self.target = 'exposure'
                self.signal_noise_ratio = [u.Quantity(x) for x in value] * u.dimensionless_unscaled
            else:
                vars(self)[name] = u.Quantity(value)
        self._calculate()

    
    def _set_source_parameter(self, name, value):
        # TODO -- input validation
        if name == 'type':
            self.source.set_type(value)
        elif name == 'wavelength_band':
            self.source.wavelength_band = str(value)
        elif name == 'brightness':
            self.source.set_brightness(value)
        elif name == 'temperature':
            self.source.temperature = u.Quantity(value).to(u.K, equivalencies=u.temperature())
        else:
            vars(self.source)[name] = u.Quantity(value)
            self._calculate()

    def _set_atmosphere_parameter(self, name, value):
        # TODO -- input validation
        vars(self.atmosphere)[name] = u.Quantity(value)
        self._calculate()
    
    def _set_instrument_parameter(self, name, value):
        # TODO -- input validation
        if name == 'name':
            self.instrument.set_name(value)
        elif name == 'mode':
            self.instrument.mode = str(value)
        else:
            vars(self.instrument)[name] = u.Quantity(value)
        self._calculate()

    def get_parameters(self):

        parameters = {
            'dithers': str(self.dithers),
            'reads': str(self.reads),
            'repeats': str(self.repeats),
            'coadds': str(self.coadds),
            'binning': self.binning.value,
            'atmosphere.seeing': str(self.atmosphere.seeing),
            'atmosphere.airmass': str(self.atmosphere.airmass),
            'atmosphere.water_vapor': str(self.atmosphere.water_vapor)
        }
        if self.target == 'signal_noise_ratio':
            parameters['exposure'] = [str(exp)+'s' for exp in self.exposure.to(u.s).value]
        elif self.target == 'exposure':
            parameters['signal_noise_ratio'] = self.signal_noise_ratio.value

        for parameter in self.source.active_parameters:
            parameters['source.'+parameter] = str(vars(self.source)[parameter])

        for parameter in self.instrument.active_parameters:
            parameters['instrument.'+parameter] = str(vars(self.instrument)[parameter])

        return parameters