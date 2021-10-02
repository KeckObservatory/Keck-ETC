from Instrument import instrument
from Atmosphere import atmosphere
from Source import source

class run_test:

    def __init__(self):

        foo = instrument('test')

        print(foo)
        print(foo.config.who)
        print(foo.config.why)
        print(foo.config.why.when)
        print(foo.config.why.how)

        bar = atmosphere()

        print(bar.config.defaults.seeing)
        print(bar.seeing)
        print(bar.airmass)
        print(bar.water_vapor)

        yum = source()