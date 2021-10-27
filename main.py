
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Panel, Select, Tabs, HoverTool, Spinner, Div
from bokeh.events import DocumentReady
from bokeh.layouts import column, row

# Import exposure time calculator
from ETC import exposure_time_calculator

from astropy import units as u


# Function definitions go here

def switchInstrument(attr, old, new):
    etc.set_instrument_parameter('name', available_instruments[new])
    #etc.instrument.set_name(available_instruments[new])

def set_quantity(id, value):
    print(f'Called to set element {id} to value {value}')
    pass  # TODO -- will call appropriate methods in etc to set value for element with id

def create_quantity(id, name, default, unit_options, unit_default):
    quantity = row(
        Spinner(title=name, value=default, width=100),
        Select(title='Unit:', value=unit_default, options=unit_options, width=100)
    )
    def unit_callback(attr, old, new):
        quantity.children[0].value = u.Quantity(str(quantity.children[0].value)+old).to(new).value

    quantity.children[0].on_change('value', 
        lambda attr, old, new: set_quantity(id, str(new)+quantity.children[1].value)  # TODO -- if unit was changed, don't call set_quantity
    )
    quantity.children[1].on_change('value', unit_callback)
    return quantity

def create_instrument(etc):
    return column(
        create_quantity(0, 'Exposure:', etc.exposure[0].value, ['us', 'ms', 's', 'min', 'hr'], str(etc.exposure[0].unit))
    )

def create_source(etc):
    return column()  # TODO

def create_atmosphere(etc):
    return column()  # TODO

def create_results(etc):
    return column()  # TODO

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
    global loaded
    global etc
    global available_instruments

    if not 'etc' in globals():
        
        etc = exposure_time_calculator()
        available_instruments = etc.config.instruments
        instruments = Tabs(
            tabs=[ Panel(child=column(), title=instrument.upper()) for instrument in available_instruments ]
        )
        dashboard = create_dashboard(etc)
        instruments.on_change('active', switchInstrument)

        curdoc().add_root(column(instruments, dashboard))



curdoc().add_root(column())
curdoc().on_event(DocumentReady, run_app)

