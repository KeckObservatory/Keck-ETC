from Instrument import instrument
from Atmosphere import atmosphere
from Source import source
import astropy.units as u
import timeit
from numpy.random import random


if __name__ == '__main__':
    foo = instrument('nires')
    foo.get_throughput(u.Quantity([5000, 8000, 10000, 11000], u.angstrom))
    foo.get_dark_current()
    foo.get_read_noise()


    bar = atmosphere()
    bar.airmass=u.Quantity(1.3)
    bar.water_vapor=u.Quantity('4.2 mm')
    bar.get_transmission(u.Quantity(random(1000)*4, u.micron))
    bar.get_emission(u.Quantity(random(1000)*4, u.micron))

    yum = source()
    yum.redshift = 2
    yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron))