from astropy import units as u
from Instrument import instrument
from Source import source
from Atmosphere import atmosphere
import yaml
from numpy import pi, arange, zeros

class etc:

    global _CONFIG_FILEPATH; _CONFIG_FILEPATH = 'config.yaml'

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

        # Check that either exposure or snr is provided
        if len(self.signal_noise_ratio) == len(self.exposure) == 0:
            raise ValueError('ERROR: In ETC -- Exactly one of S/N or exposure must be provided, found neither')


        slit_size = self.instrument.slit_width * self.instrument.slit_length
        slit_size_pixels = slit_size / self.instrument.pixel_size
        source_size = self.instrument.slit_width * self.atmosphere.seeing
        source_slit_ratio = source_size / (pi * self.atmosphere.seeing**2)

        # TODO -- coadds, reads, all the juicy details
        self.source_flux = self.source.get_flux(self.wavelengths) * self.atmosphere.get_transmission(self.wavelengths)
        source_rate =  self.source_flux * self.instrument.get_throughput(self.wavelengths)
        source_rate *= self.telescope_area * source_slit_ratio * self.wavelengths  # Why is wavelength divided by 2700 in Sherry's code?
        #Also, should we include diffraction and increase area slightly? Or is that negligible?
        self.efficiency = (self.atmosphere.get_transmission(self.wavelengths) * self.instrument.get_throughput(self.wavelengths)).value  # Save efficiency as dimensionless, not e-/ph

        # Background -- why do we subtract the area of the source? Don't we still get photon hits from the background on those pixels? Since they're not saturated (presumably), isn't that noise?
        # Also, why isn't the throughput included in Sherry's code?
        background_rate = self.atmosphere.get_emission(self.wavelengths) * self.instrument.get_throughput(self.wavelengths)
        background_rate *= self.telescope_area * (slit_size - source_size) * self.wavelengths
        

        # Exposure is desired
        if len(self.signal_noise_ratio) == 0:

            self.source_count = [source_rate * exp for exp in self.exposure] * u.electron
            self.background_count = [background_rate * exp for exp in self.exposure] * u.electron
            self.dark_current_count = [self.instrument.get_dark_current() * slit_size_pixels * exp for exp in self.exposure] * u.electron
            self.read_noise_count = ([self.instrument.get_read_noise()**2 * self.read] * len(self.exposure)) * u.electron
            noise_count = self.source_count + self.background_count + self.dark_current_count + self.read_noise_count # Total count in e- for whole slit and exposure
            self.signal_noise_ratio = (self.source_count * noise_count ** (-1/2) * self.dither ** (1/2)).value  # Remove the sqrt(e-) unit because it's nonphysical

        elif len(self.exposure) == 0:
            pass  # TODO

        else:
            # Check that exposure and S/N have not both been provided
            raise ValueError('ERROR: In ETC -- Exactly one of S/N or exposure must be provided, found both')


    def __init__(self):
        print("\033[H\033[J", end='')
        print('ETC: Initializing exposure time calculator')
        # Set default values based on config file
        self._mount_config(_CONFIG_FILEPATH)
        self._validate_config()

        # Initialize objects
        self.instrument = instrument(self.config.defaults.instrument)
        self.atmosphere = atmosphere()
        self.source = source()

        # Initialize values
        self.telescope_area = u.Quantity(self.config.telescope_area)
        self.exposure = [u.Quantity(x).to(u.s).value for x in self.config.defaults.exposure] * u.s
        self.signal_noise_ratio = [u.Quantity(x).to(u.dimensionless_unscaled).value for x in self.config.defaults.signal_noise_ratio] * u.dimensionless_unscaled
        self.dither = u.Quantity(self.config.defaults.dither)
        self.read = u.Quantity(self.config.defaults.read)
        self.repeat = u.Quantity(self.config.defaults.repeat)
        self.coadd = u.Quantity(self.config.defaults.coadd)
        # Calculate default wavelengths array from min, max of instrument and atmosphere
        min_wavelength = max(self.atmosphere.wavelength_index[0], self.instrument.min_wavelength).to(u.angstrom).value
        max_wavelength = min(self.atmosphere.wavelength_index[-1], self.instrument.max_wavelength).to(u.angstrom).value
        self.wavelengths = arange(min_wavelength, max_wavelength, (max_wavelength-min_wavelength)/self.config.defaults.default_wavelengths_number) * u.angstrom

        #self._calculate()
        # -- TESTING -- #
        self.source.set_type('flat')
        self.exposure = [10] * u.s
        import time
        start = time.time()
        test = self._calculate()
        end = time.time()
        print('TIME: ',end-start)
        print(test)