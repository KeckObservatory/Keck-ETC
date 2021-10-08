from Instrument import instrument
from Atmosphere import atmosphere
from Source import source
import astropy.units as u


if __name__ == '__main__':
    foo = instrument('nires')
    what = u.Quantity([5000, 8000, 10000, 11000], u.angstrom)
    print(foo.get_throughput(what))
    print(foo.get_dark_current())
    print(foo.get_read_noise())


    bar = atmosphere()

    yum = source()
