
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Panel, Select, Tabs, Spinner, Div, FileInput
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
        def callback(new):
            etc.set_parameter(id, new)
            update_source()
        quantity = Spinner(title=name, value=default, width=100)
        quantity.on_change('value', lambda attr, old, new: callback(new))
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
    band = create_dropdown('source.wavelength_band', 'Band:', etc.source.wavelength_band, list(vars(etc.source.config.wavelength_bands).keys()))
    brightness = Spinner(title='Brightness:', value=etc.source.brightness.value, width=100)
    units = Select(title='Unit:', value=str(etc.source.brightness.unit), options=['mag(AB)', 'mag(ST)', 'Jy', 'erg / (Angstrom cm2 s)'], width=100)  # mag(bol) throws weird errors...
    types = create_dropdown('source.type', 'Source Type:', etc.source.type, list(etc.source._functions.keys()))
    redshift = create_quantity('source.redshift', 'Redshift:', etc.source.redshift.value)
    def callback(new):
        etc.set_parameter('source.brightness', str(new) + units.value)
        update_source()
    brightness.on_change('value',
        lambda attr, old, new: callback(new)  # TODO -- if unit was changed, don't call set_quantity
    )
    def unit_callback(attr, old, new):
        # Astropy can't parse magnitudes from strings, so manually parse possible magnitude values
        unit_old = u.ABmag if old=='mag(AB)' else (u.STmag if old=='mag(ST)' else (u.m_bol if old=='mag(Bol)' else u.Unit(old)))
        unit_new = u.ABmag if new=='mag(AB)' else (u.STmag if new=='mag(ST)' else (u.m_bol if new=='mag(Bol)' else u.Unit(new)))
        brightness.value = (brightness.value * unit_old).to(unit_new, equivalencies=u.spectral_density(u.Quantity(vars(etc.source.config.wavelength_bands)[band.value]))).value
    units.on_change('value', unit_callback)
    
    upload = FileInput(accept='.txt', multiple=False)
    def file_callback(upload):
        print(len(upload.value))
        etc.source.add_template(upload.value, upload.filename)
        source_gui.children[0] = create_dropdown('source.type', 'Source Type:', etc.source.type, list(etc.source._functions.keys()))
    
    upload.on_change('filename', lambda attr, old, new: file_callback(upload))

    source_gui = column(types, row( brightness, units, band), redshift, upload, css_classes=['section'])
    #source_gui.on_change('children', lambda attr, old, new: print(attr, old[-1], new[-1]))

    # ADJUST offered inputs by type of source...
    #(create_quantity('source'+parameter, parameter, vars(etc.source)[parameter].value) for parameter in etc.source.active_parameters)
    return source_gui  # TODO -- finish method, ask Sherry about mag vs. temp, etc

def create_atmosphere(etc):
    return column(
        create_quantity('atmosphere.seeing', 'Seeing:', etc.atmosphere.seeing.value, ['arcsec', 'arcmin'], str(etc.atmosphere.seeing.unit)),
        create_quantity('atmosphere.airmass', 'Airmass:', etc.atmosphere.airmass.value),
        create_quantity('atmosphere.water_vapor', 'Water Vapor:', etc.atmosphere.water_vapor.value, ['um', 'mm', 'cm', 'm'], str(etc.atmosphere.water_vapor.unit)),
        css_classes=['section'], sizing_mode = 'scale_both',
    )  # TODO

def create_results(etc):
    global results
    results = ColumnDataSource(data = {'wavelengths': etc.wavelengths.to(u.nm).value, 'snr': etc.signal_noise_ratio[0]})
    plot = figure(title='SNR', tools='pan, wheel_zoom, hover, reset, save', active_scroll='wheel_zoom', tooltips=[('S/N','$y{0}'), ('λ (μm)','$x{0}')], width=400, height=300)
    plot.xaxis.axis_label = 'wavelengths (nm)'
    plot.yaxis.axis_label = 'signal to noise ratio'
    plot.line(x='wavelengths', y='snr', source=results)
    plot.output_backend = 'svg'
    return row(
        Div(text=r'<h3>SNR: '+str(max(etc.signal_noise_ratio[0]))+r'</h3>'),
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

