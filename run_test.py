from Instrument import instrument
from Atmosphere import atmosphere
from Source import source
import astropy.units as u
import timeit
from numpy.random import random


if __name__ == '__main__':
    foo = instrument('nires')
    #print(foo.get_throughput(u.Quantity([5000, 8000, 10000, 11000], u.angstrom)))
    #print(foo.get_dark_current())
    #print(foo.get_read_noise())


    bar = atmosphere()
    #bar.airmass=u.Quantity(1.3)
    #bar.water_vapor=u.Quantity('4 mm')
    print(bar.get_transmission(u.Quantity(random(10000)*4+1, u.micron)))
    
#     SETUP_CODE = '''
# from Atmosphere import atmosphere
# from numpy.random import random
# import astropy.units as u
# bar = atmosphere()
# bar.airmass=u.Quantity(1.3)
# bar.water_vapor=u.Quantity('4 mm')'''


#     em_test = timeit.timeit(setup=SETUP_CODE, stmt='bar.get_emission(u.Quantity(random(1000)*4+1, u.micron))', number=10000)
#     tr_test = timeit.timeit(setup=SETUP_CODE, stmt='bar.get_transmission(u.Quantity(random(1000)*4+1, u.micron))', number=10000)
#     print('EMISSION TIME:',em_test)
#     print('TRANSMISSION TIME:',tr_test)

    yum = source()
    yum.redshift = 2
    #print(yum.get_flux(u.Quantity([0.3, 0.5, 0.8, 1, 1.5, 2, 2.5, 3], u.micron)))