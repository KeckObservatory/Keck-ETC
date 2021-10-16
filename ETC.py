from astropy import units as u
from Instrument import instrument
from Source import source
from Atmosphere import atmosphere
import yaml
from numpy import pi, arange

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
        min_wavelength = max(self.atmosphere.wavelength_index[0], self.instrument.min_wavelength).to(u.angstrom).value
        max_wavelength = min(self.atmosphere.wavelength_index[-1], self.instrument.max_wavelength).to(u.angstrom).value
        wavelengths = arange(min_wavelength, max_wavelength, (max_wavelength-min_wavelength)/self.config.num_points) * u.angstrom
        # TODO -- define wavelengths by min, max accepted by components
        # TODO -- perform for range of exposures to create class parameter snr(wavelength, exposure), then provide f(x) for any one fixed variable

        slit_size = self.instrument.slit_width * self.instrument.slit_length
        slit_size_pixels = slit_size / self.instrument.pixel_size
        source_size = self.instrument.slit_width * self.atmosphere.seeing
        source_slit_ratio = source_size / (pi * self.atmosphere.seeing**2)

        # TODO -- coadds, reads, all the juicy details
        source_total = self.source.get_flux(wavelengths) * self.atmosphere.get_transmission(wavelengths) * self.instrument.get_throughput(wavelengths)
        source_total *= self.telescope_area * source_slit_ratio * self.exposure * wavelengths  # Why is wavelength divided by 2700 in Sherry's code?
        # Background -- why do we subtract the area of the source? Don't we still get photon hits from the background on those pixels? Since they're not saturated (presumably), isn't that noise?
        # Also, why isn't the throughput included in Sherry's code?
        background_total = self.atmosphere.get_emission(wavelengths) * self.instrument.get_throughput(wavelengths)
        background_total *= self.telescope_area * (slit_size - source_size) * self.exposure * wavelengths

        # print(source_total.unit)
        # print(background_total.unit)
        # print((self.instrument.get_dark_current() * slit_size_pixels * self.exposure).units)
        # print((self.instrument.get_read_noise()**2 * slit_size_pixels * self.exposure).units)
        noise_total = source_total + background_total
        noise_total += self.instrument.get_dark_current() * slit_size_pixels * self.exposure
        noise_total += self.instrument.get_read_noise()**2 * self.read


        # TODO -- set class parameters, don't return anything, get_results will be another method taking in any combination of exp, snr, wav and returning appropriate results!
        # Also remember to keep track of source, bg, dark current and read noise separately for plotting & analysis!
        return (source_total).to(u.electron) / (noise_total).to(u.electron)**.5


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
        self.exposure = u.Quantity(self.config.defaults.exposure)
        #self.snr = u.Quantity(self.config.defaults.snr)
        self.dither = u.Quantity(self.config.defaults.dither)
        self.read = u.Quantity(self.config.defaults.read)
        self.repeat = u.Quantity(self.config.defaults.repeat)
        self.coadd = u.Quantity(self.config.defaults.coadd)

        #self._calculate()
        # -- TESTING -- #
        self.source.set_type('flat')
        self.exposure = 10 * u.s
        import time
        start = time.time()
        test = self._calculate()
        end = time.time()
        print('TIME: ',end-start)
        print(test)