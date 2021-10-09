from Instrument import instrument
from Atmosphere import atmosphere
from Source import source
import astropy.units as u


if __name__ == '__main__':
    foo = instrument('nires')
    print(foo.get_throughput(u.Quantity([5000, 8000, 10000, 11000], u.angstrom)))
    print(foo.get_dark_current())
    print(foo.get_read_noise())

    bar = atmosphere()

    yum = source()
    yum.redshift = 2
    print(yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron)))