from Instrument import instrument
from Atmosphere import atmosphere
from Source import source
import astropy.units as u
from ETC import exposure_time_calculator
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
    

    # TESTING FITS vs. ASCII FILE SPEED!!

    from os import listdir
    from astropy.table import Table
    import numpy as np
    import astropy.units as u


    water_vapor_index = [u.Quantity(x).to(u.mm).value for x in  ['1 mm', '1.6 mm', '3 mm', '5 mm']] * u.mm
    airmass_index = u.Quantity([1.0, 1.5, 2.0])
    wavelength_index = [u.Quantity(x).to(u.angstrom) for x in ['0.9 um', '5.6 um', '0.02 nm']]
    wavelength_index = np.arange(
        u.Quantity(wavelength_index[0]).value,
        u.Quantity(wavelength_index[1]).value,
        u.Quantity(wavelength_index[2]).value
    ) * u.angstrom

    transmission = np.zeros([len(airmass_index), len(water_vapor_index), len(wavelength_index)])
    emission = np.zeros([len(airmass_index), len(water_vapor_index), len(wavelength_index)])

    for i, filename in enumerate(listdir('./sky_background')):
        try:
            if filename.startswith('mktrans') or filename.startswith('mk_skybg'):
                data = Table.read('./sky_background/'+filename, format='ascii.ecsv')
                data.meta['vapor'] = data.meta.pop('water_vapor')
                data.write('./sky_background/'+filename.split('.')[0]+'.fits', format='fits')
        except ValueError:
            pass

