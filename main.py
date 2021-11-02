
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Panel, Select, Tabs, Spinner, Div, FileInput, Paragraph, CustomJS, Slider, CheckboxGroup
from bokeh.events import DocumentReady
from bokeh.layouts import column, row

# Import exposure time calculator
from ETC import exposure_time_calculator
from numpy import linspace
from astropy import units as u
import pdb


# Function definitions go here

def update_results():
    global exposure_slider
    global results
    index = abs(etc.exposure.value - exposure_slider.value) == min(abs(etc.exposure.value - exposure_slider.value))
    results.data = {'wavelengths': etc.wavelengths.to(u.nm).value, 'snr': etc.signal_noise_ratio[index].flatten().value}

def create_quantity(id, name, default, unit_options=None, unit_default=None, js_callback=None, increment=1, low=None, high=None, equivalency=None):
    if unit_options is None and unit_default is None:
        def callback(quantity,old,new):
            try:
                etc.set_parameter(id, new)
            except ValueError:
                if js_callback is not None:
                    quantity.tags = ['js_callback_tag_true'] if quantity.tags==['js_callback_tag_false'] else ['js_callback_tag_false']
                quantity.value = old
            update_results()
        quantity = Spinner(title=name, value=default, width=100, step=increment, low=low, high=high)
        quantity.on_change('value', lambda attr, old, new: callback(quantity, old, new))
        if js_callback is not None:
            quantity.js_on_change('tags', js_callback)
    else:
        quantity = row(
            Spinner(title=name, value=default, width=100, step=increment, low=low, high=high),
            Select(title='\u00A0', value=unit_default, options=unit_options, width=100)
        )
        def unit_callback(attr, old, new):
                quantity.children[0].value = u.Quantity(str(quantity.children[0].value)+old).to(new, equivalencies=equivalency).value

        def callback(number, old, new):
            try:
                etc.set_parameter(id, str(new) + quantity.children[1].value)
            except ValueError:
                if js_callback is not None:
                    number.tags = ['js_callback_tag_true'] if number.tags==['js_callback_tag_false'] else ['js_callback_tag_false']
                number.value = old
            update_results()

        quantity.children[0].on_change('value',
            lambda attr, old, new: callback(quantity.children[0], old, new)  # TODO -- if unit was changed, don't call set_quantity
        )
        quantity.children[1].on_change('value', unit_callback)

        if js_callback is not None:
           quantity.children[0].js_on_change('tags', js_callback)
    return quantity

def create_dropdown(id, name, default, options):
    def callback(new):
        etc.set_parameter(id, new)
        update_results()
    dropdown = Select(title=name, value=default, options=options, width=100)
    dropdown.on_change('value', lambda attr, old, new: callback(new))
    return dropdown

def create_instrument(etc):
    exposure_label = Paragraph(text='Exposure:', margin=(5, 5, 0, 5))
    exposure_min = Spinner(title='Min:', value=etc.exposure[0].value, width=100, low=0)
    exposure_max = Spinner(title='Max:', value=etc.exposure[-1].value, width=100, low=exposure_min.value)
    units = Select(title='\u00A0', value=str(etc.exposure.unit), options=['ms', 's', 'min', 'hr'], width=100)

    def callback(attr, old, new):
        print(attr, old, new)
        exposure_list = linspace(exposure_min.value, exposure_max.value, 100)  if exposure_max.value > exposure_min.value else [exposure_min.value]# Hard-coded for now, change later!!
        etc.set_parameter('exposure', [str(exp)+units.value for exp in exposure_list])
        if len(exposure_list) > 1:
            exposure_slider.title = 'Exposure ('+units.value+')'
            exposure_slider.start = etc.exposure[0].to(units.value).value
            exposure_slider.end = etc.exposure[-1].to(units.value).value
            exposure_slider.step = (etc.exposure[1].to(units.value) - etc.exposure[0].to(units.value)).value if len(etc.exposure) > 1 else 0
            exposure_slider.value = etc.exposure[0].to(units.value).value
            exposure_slider.visible = True
        else:
            exposure_slider.visible = False
        update_results()

    exposure_min.on_change('value', callback)
    exposure_max.on_change('value', callback)

    def unit_callback(attr, old, new):
        exposure_min.value = (exposure_min.value * u.Unit(old)).to(new).value
        exposure_max.low = exposure_min.value
        exposure_max.value = (exposure_max.value * u.Unit(old)).to(new).value

    units.on_change('value', unit_callback)

    return column(
        exposure_label,
        row(exposure_min, exposure_max, units),
        css_classes=['section'],
        name='exposure_panel'
    )

def create_source(etc):
    band = create_dropdown('source.wavelength_band', 'Band:', etc.source.wavelength_band, list(vars(etc.source.config.wavelength_bands).keys()))
    brightness = Spinner(title='Brightness:', value=etc.source.brightness.value, width=100, low=0)
    units = Select(title='\u00A0', value=str(etc.source.brightness.unit), options=['mag(AB)', 'mag(ST)', 'Jy', 'erg / (Angstrom cm2 s)'], width=100)  # mag(bol) throws weird conversion errors, but could be re-implemented later
    types = create_dropdown('source.type', 'Source Type:', etc.source.type, list(etc.source._functions.keys()))
    redshift = create_quantity('source.redshift', 'Redshift:', etc.source.redshift.value)
    def callback(new):
        etc.set_parameter('source.brightness', str(new) + units.value)
        update_results()
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
        etc.source.add_template(upload.value, upload.filename)
        source_gui.children[0] = create_dropdown('source.type', 'Source Type:', etc.source.type, list(etc.source._functions.keys()))
    
    upload.on_change('filename', lambda attr, old, new: file_callback(upload))
    upload_label = Paragraph(text='Upload spectrum (ECSV):', margin=(5, 5, 0, 5))
    # Add everthing to a column
    source_gui = column(types, row( brightness, units, band), redshift, css_classes=['section'], name='source_panel')
    
    # Optional parameters defined and added, if present
    if 'fwhm' in etc.source.active_parameters:
        source_gui.children.append(create_quantity('source.fwhm', 'FWHM:', etc.source.fwhm.value, ['Angstrom', 'nm', 'um', 'mm'], str(etc.source.fwhm.unit), low=0))
    if 'temperature' in etc.source.active_parameters:
        # To include options for fahrenheit and rankine, need 'u.imperial.enable()' in here and ETC.py... check w/ Sherry!
        source_gui.children.append(create_quantity('source.temperature', 'Temperature:', etc.source.temperature.value, ['K', 'deg_C'], str(etc.source.temperature.unit), equivalency=u.temperature()))
    if 'index' in etc.source.active_parameters:
        source_gui.children.append(create_quantity('source.index', 'Power Index:', etc.source.index.value))

    
    # ADJUST offered inputs by type of source...
    #(create_quantity('source'+parameter, parameter, vars(etc.source)[parameter].value) for parameter in etc.source.active_parameters)
    source_gui.children.append(upload_label)
    source_gui.children.append(upload)
    return source_gui  # TODO -- finish method, ask Sherry about mag vs. temp, etc

def create_atmosphere(etc):
    js_callback_code = """alert(name+' requires a value between '+min+' and '+max+' '+units);"""
    airmass_callback = CustomJS(args=dict(name='Airmass', min=etc.atmosphere._airmass_index[0].value, 
        max=etc.atmosphere._airmass_index[-1].value, units=str(etc.atmosphere.airmass.unit)),
         code=js_callback_code)
    water_vapor_callback = CustomJS(args=dict(name='Water vapor', min=etc.atmosphere._water_vapor_index[0].value, 
        max=etc.atmosphere._water_vapor_index[-1].value, units=str(etc.atmosphere.water_vapor.unit)), code=js_callback_code)

    return column(
        create_quantity('atmosphere.seeing', 'Seeing:', etc.atmosphere.seeing.value, ['arcsec', 'arcmin'], str(etc.atmosphere.seeing.unit), increment=0.1, low=0),
        create_quantity('atmosphere.airmass', 'Airmass:', etc.atmosphere.airmass.value, js_callback=airmass_callback, increment=0.1),
        create_quantity('atmosphere.water_vapor', 'Water Vapor:', etc.atmosphere.water_vapor.value, ['um', 'mm', 'cm', 'm'], str(etc.atmosphere.water_vapor.unit), js_callback=water_vapor_callback, increment=0.5),
        css_classes=['section'], sizing_mode = 'scale_both', name='atmosphere_panel'
    )  # TODO

def create_results(etc):
    global results
    global exposure_slider
    results = ColumnDataSource(data = {'wavelengths': etc.wavelengths.to(u.nm).value, 'snr': etc.signal_noise_ratio[0].value})
    step_size = (etc.exposure[1] - etc.exposure[0]).value if len(etc.exposure) > 1 else 0
    exposure_slider = Slider(start=etc.exposure[0].value, end=etc.exposure[-1].value, step=step_size, value=etc.exposure[0].value, title='Exposure ('+str(etc.exposure.unit)+')') if len(etc.exposure) > 1 else Slider(start=0, end=1, step=1, value=0, visible=False)
    exposure_slider.on_change('value', lambda attr, old, new: update_results())
    plot = figure(title='SNR', tools='pan, wheel_zoom, hover, reset, save', active_scroll='wheel_zoom', tooltips=[('S/N','$y{0}'), ('λ (μm)','$x{0}')], width=400, height=300)
    plot.xaxis.axis_label = 'wavelengths (nm)'
    plot.yaxis.axis_label = 'signal to noise ratio'
    plot.line(x='wavelengths', y='snr', source=results)
    plot.output_backend = 'svg'
    return row(
        column(
            plot,
            exposure_slider
        ), name='results'
    )  # TODO

def create_dashboard(etc):
    curdoc().add_root(create_instrument(etc))
    curdoc().add_root(create_atmosphere(etc))
    curdoc().add_root(create_results(etc))
    source = create_source(etc)
    def source_callback(source):
        source = create_source(etc)
        source.children[0].on_change('value', lambda attr, old, new: source_callback(source))
    source.children[0].on_change('value', lambda attr, old, new: source_callback(source))
    curdoc().add_root(source)


# Main code goes here

def run_app(event):
    # With objects, after loading etc, call instruments_menu.update() method, which will work for each class that I create!
    global etc
    global available_instruments

    if 'etc' not in globals():
        
        etc = exposure_time_calculator()
        available_instruments = etc.config.instruments
        instruments = Tabs(
            tabs=[ Panel(child=Div(), title=instrument.upper()) for instrument in available_instruments ], name='instruments'
        )
        create_dashboard(etc)
        instruments.on_change('active', lambda attr, old, new: etc.set_parameter('instrument.name', available_instruments[new]))

        curdoc().add_root(instruments)




# To make add_root work, initialize objects (instrument_menu, source_panel, etc.) and add their results.value --> column(), which will start empty and then be updated as everything loads!
curdoc().add_root(Div(name='instruments'))
curdoc().add_root(Div(name='exposure_panel'))
curdoc().add_root(Div(name='source_panel'))
curdoc().add_root(Div(name='atmosphere_panel'))
curdoc().add_root(Div(name='results'))
curdoc().on_event(DocumentReady, run_app)

