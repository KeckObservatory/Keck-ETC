import astropy.units as u
from calculator.ETC import exposure_time_calculator as etc
from numpy.random import random


if __name__ == '__main__':
    # foo = instrument('nires')
    # foo.get_throughput(u.Quantity([5000, 8000, 10000, 11000], u.angstrom))
    # foo.get_dark_current()
    # foo.get_read_noise()


    # bar = atmosphere()
    # bar.airmass=u.Quantity(1.3)
    # bar.water_vapor=u.Quantity('4.2 mm')
    # bar.get_transmission(u.Quantity(random(1000)*4, u.micron))
    # bar.get_emission(u.Quantity(random(1000)*4, u.micron))

    # yum = source()
    # yum.redshift = 2
    # yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron))
    # yum.set_type('blackbody')
    # yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron))
    # yum.set_type('flat')
    # yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron))
    # yum.set_type('power')
    # yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron))
    # yum.set_type('qso')
    # yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron))
    # yum.set_type('seyfert1')
    # yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron))
    # yum.set_type('seyfert2')
    # yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron))
    # yum.set_type('vega')
    # yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron))
    # yum.set_type('gaussian')
    # yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron))

    # test = exposure_time_calculator()
    # test.set_source_parameter('type', 'vega')
    # test.set_parameter('exposure', [10] * u.s)
    # test.set_parameter('wavelengths', u.Quantity([20000], u.angstrom))
    # snr = test.signal_noise_ratio.flatten()
    # print(snr)
    # print(test.source_count)
    # print(test.background_count)
    # print(test.dark_current_count)
    # print(test.read_noise_count)
    # test.set_parameter('signal_noise_ratio', snr * u.dimensionless_unscaled)
    # print(test.exposure)
    t = etc()
    t.set_parameter('wavelengths', [1]*u.um)
    t.set_parameter('exposure', [33333333] * u.s)
    snr = t.signal_noise_ratio[0][0].value
    t.set_parameter('signal_noise_ratio', [snr])
    print(t.exposure)