from astropy import units as u
from Instrument import instrument
from Source import source
from Atmosphere import atmosphere
import yaml
from numpy import pi, linspace, zeros, array, arccos, sqrt, NaN
from warnings import warn
from json import loads as json_loads

class exposure_time_calculator:

    global _CONFIG_FILEPATH; _CONFIG_FILEPATH = './calculator/config.yaml'

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

        source_rate = self.source_flux * self.instrument.get_throughput(self.wavelengths) * self.instrument.binning[0] * self.instrument.binning[1]  # Binning in the spectral direction
        source_rate *= self.telescope_area * source_slit_ratio * (self.wavelengths / self.instrument.spectral_resolution)


        background_rate = self.atmosphere.get_emission(self.wavelengths) * self.instrument.get_throughput(self.wavelengths) * self.instrument.binning[0] * self.instrument.binning[1]
        background_rate *= self.telescope_area * slit_size * (self.wavelengths / self.instrument.spectral_resolution)
        # Divide reads by 2 because read noise is per CDS (2 reads)
        read_noise = self.instrument.get_read_noise()**2 * slit_size_pixels / sqrt(self.reads) / self.instrument.binning[0]  # Binning in the spatial direction

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
            self.integration_time = [(number_exposures * exp) for exp in self.exposure] * u.s

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
            self.integration_time = zeros([len(self.signal_noise_ratio), len(self.wavelengths)])

            for idx, snr in enumerate(self.signal_noise_ratio.value * u.electron**(1/2)):

                # Define a, b, c for quadratic formula
                # Adding 0j to avoid generating RuntimeWarning for sqrt(-1)
                a = source_rate**2 + 0j
                b = - snr**2 * (background_rate + dark_current_rate + source_rate) / number_exposures + 0j
                c = [ (-read_noise * snr**2 / number_exposures).to(u.electron**2).value ] * len(self.wavelengths) * u.electron**2 + 0j


                # Quadratic formula
                exposure_pos = ( -b + (b**2 - 4*a*c)**(1/2) ) / (2 * a)
                exposure_neg = ( -b - (b**2 - 4*a*c)**(1/2) ) / (2 * a)
                
                # This statement is broken, iter() needs to be moved outside because it reinitializes every time
                iter_exp_pos = iter(exposure_pos)
                iter_exp_neg = iter(exposure_neg)
                exposure = [next(iter_exp_pos) if check else next(iter_exp_neg) for check in (exposure_pos.real >= 0) & (exposure_pos.imag == 0)] * u.s
                if ((exposure.real < 0) | (exposure.imag != 0)).any():
                    exposure[(exposure.real < 0) | (exposure.imag != 0)] = NaN
                    warn('In ETC -- Some/all solutions do not exist for S/N = '+str(snr.value)+', returning exposure = NaN', RuntimeWarning)
                self.integration_time[idx, :] = exposure.real.to(u.s)

            self.integration_time = u.Quantity(self.integration_time, u.s)  # Convert ndarray to quantity
            # Get length of single exposure
            self.exposure = [(t / number_exposures) for t in self.integration_time] * u.s

            # Calculate and save counts based on calculated exposure = f(wavelength)
            self.source_count_adu = [source_rate * self.instrument.pixel_size / source_size * exp * number_exposures / self.instrument.gain for exp in self.exposure] * (u.adu/u.pixel)
            self.background_count_adu = [background_rate / slit_size * self.instrument.pixel_size * exp * number_exposures / self.instrument.gain for exp in self.exposure] * (u.adu/u.pixel)
            self.dark_current_count_adu = [dark_current_rate / slit_size_pixels * exp * number_exposures / self.instrument.gain for exp in self.exposure] * (u.adu/u.pixel)
            self.read_noise_count_adu = ([[(read_noise / slit_size_pixels * number_exposures / self.instrument.gain).to(u.adu/u.pixel).value] * len(self.wavelengths)] * len(self.exposure)) * (u.adu/u.pixel)

        else:
            # Check that etc has a valid target set
            raise ValueError('ERROR: In ETC -- target must be set to "exposure" or "signal_noise_ratio"')

        # Save total counts
        self.total_count_adu = self.source_count_adu + self.background_count_adu + self.dark_current_count_adu + self.read_noise_count_adu
        # Save clock time, efficiency
        self.clock_time = self.integration_time * NaN
        self.efficiency = self.integration_time / self.clock_time


    def reset_parameters(self):

        # Initialize values
        self.telescope_area = u.Quantity(self.config.telescope_area)
        self.exposure = [u.Quantity(x) for x in self.config.defaults.exposure] * u.s
        self.signal_noise_ratio = [u.Quantity(x) for x in self.config.defaults.signal_noise_ratio] * u.dimensionless_unscaled
        self.dithers = u.Quantity(self.config.defaults.dithers)
        self.reads = u.Quantity(self.config.defaults.reads)
        self.repeats = u.Quantity(self.config.defaults.repeats)
        self.coadds = u.Quantity(self.config.defaults.coadds)
        self.target = self.config.defaults.target

        # Reset objects
        self.instrument.set_parameter('name', self.config.defaults.instrument)
        # Calculate default wavelengths array from min, max of instrument
        self.wavelengths = linspace(self.instrument.min_wavelength, self.instrument.max_wavelength, self.config.defaults.default_wavelengths_number).to(u.angstrom)

        self.atmosphere.reset_parameters()
        self.source.reset_parameters()


    def __init__(self):
        # Set default values based on config file
        self._mount_config(_CONFIG_FILEPATH)
        self._validate_config()

        # Initialize objects
        self.instrument = instrument(self.config.defaults.instrument)
        self.atmosphere = atmosphere()
        self.source = source()
        u.add_enabled_units([self.source.flam, self.source.photlam])
        u.imperial.enable()

        self.reset_parameters()

        self._calculate()

    def set_parameters(self, parameters):
        # Validate input format
        if isinstance(parameters, str):
            try:
                parameters = json_loads(parameters)
            except ValueError:
                raise ValueError('In ETC.set_parameters() -- parameters is not a valid dictionary or json-like string')
        elif not isinstance(parameters, dict):
            raise ValueError('In ETC.set_parameters() -- parameters is not a valid dictionary or json-like string')

        # Set each parameter, then calculate results
        errors = ''
        # Handle b64 values first, removing the indicator 'b64' from key
        for key, val in [ (key, val) for key, val in parameters.items() if 'b64' in key]:
            try:
                self.set_parameter(key.replace('b64',''), val, run_calculator=False)
                parameters.pop(key)
            except Exception as e:
                errors += str(e).split(' -- ')[-1] + '\n'
        # Set all other values
        for key, val in parameters.items():
            try:
                self.set_parameter(key, val, run_calculator=False)
            except Exception as e:
                errors += str(e).split(' -- ')[-1] + '\n'

        self._calculate()
        if len(errors) > 0:
            raise ValueError(f'In ETC.set_parameters() -- encountered the following errors: \n{errors}')


    def set_parameter(self, name, value, run_calculator=True):

        # Aliases for instrument name and source type
        if name == 'instrument':
            name = 'instrument.name'
        elif name == 'source':
            name = 'source.type'

        # Parameter belongs to other class
        if name not in vars(self).keys():

            # Coerce parameter name, if applicable
            if name in vars(self.instrument).keys():
                warn(f'In ETC.set_parameter() -- coercing parameter {name} to instrument.{name}')
                name = 'instrument.' + name
            elif name in vars(self.source).keys():
                warn(f'In ETC.set_parameter() -- coercing parameter {name} to source.{name}')
                name = 'source.' + name
            elif name in vars(self.atmosphere).keys():
                warn(f'In ETC.set_parameter() -- coercing parameter {name} to atmosphere.{name}')
                name = 'atmosphere.' + name
            
            # Assign parameter to appropriate place
            if name.startswith('instrument.'):
                self.instrument.set_parameter(name.replace('instrument.',''), value)
                # Calculate default wavelengths array from min, max of instrument
                self.wavelengths = linspace(self.instrument.min_wavelength, self.instrument.max_wavelength, self.config.defaults.default_wavelengths_number).to(u.angstrom)
                # If setting a different instrument, reset wavelength band and wavelengths according to instrument defaults
                if name == 'instrument.name':
                    # Set default wavelength band according to range of instrument
                    self.source.set_parameter('wavelength_band', self.instrument.config.defaults.wavelength_band)
            elif name.startswith('source.'):
                self.source.set_parameter(name.replace('source.',''), value)
            elif name.startswith('atmosphere.'):
                self.atmosphere.set_parameter(name.replace('atmosphere.',''), value)
            else:
                # Throw error if invalid name
                raise ValueError(f'In ETC.set_parameter() -- invalid parameter {name}')

        # TODO -- validation
        
        else:

            if name == 'target':
                if value != 'signal_noise_ratio' and value != 'exposure':
                    raise ValueError('In ETC.set_parameter() -- target must be either "exposure" or "signal_noise_ratio"')
                if value == 'exposure' and self.target == 'signal_noise_ratio':
                    self.signal_noise_ratio = [u.Quantity(x) for x in self.config.defaults.signal_noise_ratio] * u.dimensionless_unscaled
                elif value == 'signal_noise_ratio' and self.target == 'exposure':
                    self.exposure = [u.Quantity(x) for x in self.config.defaults.exposure] * u.s
                self.target = value
            elif name == 'wavelengths':
                if isinstance(value, str):
                    value = [value]
                elif not isinstance(value, list):
                    value = list(value)
                self.wavelengths = [u.Quantity(x).to(u.angstrom) for x in value] * u.angstrom
            elif name == 'exposure':
                if isinstance(value, str):
                    value = [value]
                elif not isinstance(value, list):
                    value = list(value)
                self.target = 'signal_noise_ratio'
                self.exposure = [u.Quantity(x).to(u.s) for x in value] * u.s
            elif name == 'signal_noise_ratio':
                if isinstance(value, str):
                    value = [value]
                elif not isinstance(value, list):
                    value = list(value)
                self.target = 'exposure'
                self.signal_noise_ratio = [u.Quantity(x) for x in value] * u.dimensionless_unscaled
            else:
                vars(self)[name] = u.Quantity(value)
        
        if run_calculator:
            self._calculate()

    def get_parameters(self):
        # Define method to format data
        def construct_parameters(obj, names):
            parameters = {}
            for name in names:
                if isinstance(vars(obj)[name], u.Quantity):
                    if vars(obj)[name].size > 1:
                        parameters[name] = { 'value': vars(obj)[name].value.tolist() }
                    else:
                        parameters[name] = { 'value': vars(obj)[name].value }
                    if vars(obj)[name].unit != u.dimensionless_unscaled:
                        parameters[name]['unit'] = str(vars(obj)[name].unit)
                else:
                    parameters[name] = { 'value': vars(obj)[name]}
                
                # Look for available options in config
                options = None
                if name+'_options' in vars(obj.config).keys():
                    options = vars(obj.config)[name+'_options']
                # Since instrument config is arranged differently, check for options under config.mode
                if self.instrument.mode in vars(obj.config).keys() and name+'_options' in vars(vars(obj.config)[self.instrument.mode]).keys():
                    options = vars(vars(obj.config)[self.instrument.mode])[name+'_options']
                
                if isinstance(options, list):
                    if len(options) > 0 and isinstance(options[0], list):
                        parameters[name]['options'] = [ {'value': [u.Quantity(option[0]).value, u.Quantity(option[1]).value]} for option in options ]
                        if u.Quantity(options[0][0]).unit != u.dimensionless_unscaled:
                            parameters[name]['unit'] = str(u.Quantity(options[0][0]).unit)
                    else:
                        parameters[name]['options'] = [ {'value': option} for option in options ]
                elif options is not None:
                    parameters[name]['options'] = [ {'value': x} for x in vars(options).keys()]
            return parameters

        # Add self parameters
        parameters = construct_parameters(self, self.instrument.config.exposure_options)
        parameters['target'] = {'value': self.target, 'options': [{'value':'signal_noise_ratio', 'name':'Signal to Noise Ratio'}, {'value':'exposure','name':'Exposure'}]}
        if self.target == 'signal_noise_ratio':
            parameters['exposure'] = {'value': self.exposure.value.tolist(), 'unit': str(self.exposure.unit)}
        elif self.target == 'exposure':
            parameters['signal_noise_ratio'] = {'value': self.signal_noise_ratio.value.tolist()}

        # Add parameters for atmosphere, source, instrument
        parameters.update(construct_parameters(self.atmosphere, ['seeing', 'airmass', 'water_vapor']))
        parameters.update(construct_parameters(self.source, self.source.active_parameters))
        parameters.update(construct_parameters(self.instrument, self.instrument.active_parameters))
        # Add instrument name
        parameters['name'] = { 'value': self.instrument.name }
        # Update source type
        parameters['type']['options'] = [{'value': x, 'name': vars(self.source.config.source_types)[x].name} 
                                        if 'name' in vars(vars(self.source.config.source_types)[x]).keys() 
                                        else {'value': x} for x in self.source.available_types]
        # Update instrument slit
        for slit in parameters['slit']['options']:
            slit['name'] = f'{slit["value"][0]}" x {slit["value"][1]}"'
        if vars(self.instrument.config)[self.instrument.mode].custom_slits:
            parameters['slit']['options'] += [{'value': 'Custom'}]
        # Format wavelength band so that { value: K, options: [K,...] } --> { value: 21900, options: [ {name: K, value: 21900}, ... ] }
        options = { key: val for key, val in vars(self.source.config.wavelength_band_options).items() if self.wavelengths[0] <= u.Quantity(val) <= self.wavelengths[-1] }
        if self.source.wavelength_band not in options.keys():
            options[self.source.wavelength_band] = vars(self.source.config.wavelength_band_options)[self.source.wavelength_band]
        parameters['wavelength_band']['value'] = round(u.Quantity(options[parameters['wavelength_band']['value']]).to(u.angstrom).value)
        parameters['wavelength_band']['options'] = [{ 'name': band, 'value': round(u.Quantity(wavelength).to(u.angstrom).value) } for band, wavelength in options.items() ]


        return parameters