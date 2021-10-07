from Instrument import instrument
from Atmosphere import atmosphere
from Source import source


if __name__ == '__main__':
    foo = instrument('deimos')
    print(foo.get_throughput([5000,6000,7000, 800, 9000, 4000.48]))
    foo.amplifier = '3B'
    print(foo.get_dark_current())
    print(foo.get_read_noise())


    bar = atmosphere()

    yum = source()
