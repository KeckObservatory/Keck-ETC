
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Panel, Select, Tabs, HoverTool, Spinner, Div, Text
from bokeh.events import DocumentReady
from bokeh.layouts import column, row

# Import exposure time calculator
from ETC import exposure_time_calculator

from astropy import units as u


# Function definitions go here

def update_source():
    global results
    results.data = {'wavelengths': etc.wavelengths.to(u.nm).value, 'snr': etc.signal_noise_ratio[0]}

def create_quantity(id, name, default, unit_options=None, unit_default=None):
    if unit_options is None and unit_default is None:
        quantity = Spinner(title=name, value=default, width=100)
        quantity.on_change('value', lambda attr, old, new: etc.set_parameter(id, new))
    else:
        quantity = row(
            Spinner(title=name, value=default, width=100),
            Select(title='Unit:', value=unit_default, options=unit_options, width=100)
        )
        def unit_callback(attr, old, new):
            quantity.children[0].value = u.Quantity(str(quantity.children[0].value)+old).to(new).value

        def callback(new):
            etc.set_parameter(id, str(new) + quantity.children[1].value)
            update_source()

        quantity.children[0].on_change('value',
            lambda attr, old, new: callback(new)  # TODO -- if unit was changed, don't call set_quantity
        )
        quantity.children[1].on_change('value', unit_callback)
    return quantity

def create_dropdown(id, name, default, options):
    def callback(new):
        etc.set_parameter(id, new)
        update_source()
    dropdown = Select(title=name, value=default, options=options, width=100)
    dropdown.on_change('value', lambda attr, old, new: callback(new))
    return dropdown

def create_instrument(etc):
    return column(
        create_quantity('exposure', 'Exposure:', etc.exposure[0].value, ['us', 'ms', 's', 'min', 'hr'], str(etc.exposure[0].unit)),
        css_classes=['section'],
    )

def create_source(etc):
    return column(
        create_dropdown('source.type', 'Source Type:', etc.source.type, list(vars(etc.source.config.source_types).keys())),
        row(
            create_quantity('source.brightness', 'Brightness:', etc.source.brightness.value, ['AB', 'Jy', 'erg / (Angstrom cm2 s)'], str(etc.source.brightness.unit)),
            create_dropdown('source.wavelength_band', 'Band:', etc.source.wavelength_band, list(vars(etc.source.config.wavelength_bands).keys()))
        ),
        create_quantity('source.redshift', 'Redshift:', etc.source.redshift.value),
        css_classes=['section'],
        #(create_quantity('source'+parameter, parameter, vars(etc.source)[parameter].value) for parameter in etc.source.active_parameters)
    )  # TODO -- finish method, ask Sherry about mag vs. temp, etc

def create_atmosphere(etc):
    return column(
        create_quantity('atmosphere.seeing', 'Seeing:', etc.atmosphere.seeing.value, ['arcsec', 'arcmin'], str(etc.atmosphere.seeing.unit)),
        create_quantity('atmosphere.airmass', 'Airmass:', etc.atmosphere.airmass.value),
        create_quantity('atmosphere.water_vapor', 'Water Vapor:', etc.atmosphere.water_vapor.value, ['um', 'mm', 'cm', 'm'], str(etc.atmosphere.water_vapor.unit)),
        css_classes=['section'],
    )  # TODO

def create_results(etc):
    global results
    results = ColumnDataSource(data = {'wavelengths': etc.wavelengths.to(u.nm).value, 'snr': etc.signal_noise_ratio[0]})
    plot = figure(title='SNR', tools='crosshair, pan, reset, save, wheel_zoom', width=400, height=300)
    plot.xaxis.axis_label = 'wavelengths (nm)'
    plot.yaxis.axis_label = 'signal to noise ratio'
    plot.line(x='wavelengths', y='snr', source=results)
    return row(
        Div(text=r'<h3>SNR: '+str(max(etc.signal_noise_ratio[0]))+'</h3>'),
        plot

    )  # TODO

def create_dashboard(etc):
    return column(
        row(
            create_instrument(etc), create_source(etc), create_atmosphere(etc)
        ),
        row(
            create_results(etc)
        )
    )




# Main code goes here

def run_app(event):
    global etc
    global available_instruments

    if 'etc' not in globals():
        
        etc = exposure_time_calculator()
        available_instruments = etc.config.instruments
        instruments = Tabs(
            tabs=[ Panel(child=column(), title=instrument.upper()) for instrument in available_instruments ]
        )
        dashboard = create_dashboard(etc)
        instruments.on_change('active', lambda attr, old, new: etc.set_parameter('instrument.name', available_instruments[new]))

        curdoc().add_root(column(instruments, dashboard))



curdoc().add_root(column())
curdoc().on_event(DocumentReady, run_app)

