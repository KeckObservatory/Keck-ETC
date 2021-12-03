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
    
    photlam = u.photon/(u.cm**2 * u.s * u.angstrom)
    flam = u.erg/(u.cm**2 * u.s * u.angstrom)
    s = source()
    # TEST FLAM
    t = (1*flam).to(s.vegamag, equivalencies=s.spectral_density_vega(1*u.um))
    it = t.to(flam, equivalencies=s.spectral_density_vega(1*u.um))
    print(1*flam, t, it)
    t = (1*s.vegamag).to(flam, equivalencies=s.spectral_density_vega(1*u.um))
    it = t.to(s.vegamag, equivalencies=s.spectral_density_vega(1*u.um))
    print(1*s.vegamag, t, it)
    # TEST JANKSY
    t = (1*u.Jy).to(s.vegamag, equivalencies=s.spectral_density_vega(1*u.um))
    it = t.to(u.Jy, equivalencies=s.spectral_density_vega(1*u.um))
    print(1*u.Jy, t, it)
    t = (1*s.vegamag).to(u.Jy, equivalencies=s.spectral_density_vega(1*u.um))
    it = t.to(s.vegamag, equivalencies=s.spectral_density_vega(1*u.um))
    print(1*s.vegamag, t, it)
    # TEST STMAG
    t = (1*s.vegamag).to(u.ST, equivalencies=s.spectral_density_vega(1*u.um))
    it = t.to(s.vegamag, equivalencies=s.spectral_density_vega(1*u.um))
    print(1*s.vegamag, t, it)
    t = (1*u.STmag).to(u.ST).to(s.vegamag, equivalencies=s.spectral_density_vega(1*u.um))
    it = t.to(u.STmag, equivalencies=s.spectral_density_vega(1*u.um))
    print(1*u.STmag, t, it)
    # TEST ABMAG
    t = (1*u.ABmag).to(s.vegamag, equivalencies=s.spectral_density_vega(1*u.um))
    it = t.to(u.ABmag, equivalencies=s.spectral_density_vega(1*u.um))
    print(1*u.ABmag, t, it)
    t = (1*s.vegamag).to(u.ABmag, equivalencies=s.spectral_density_vega(1*u.um))
    it = t.to(s.vegamag, equivalencies=s.spectral_density_vega(1*u.um))
    print(1*s.vegamag, t, it)
    
    