
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Panel, Select, Tabs, Spinner, Div, FileInput, Paragraph, CustomJS, Slider, CDSView, CustomJSFilter
from bokeh.events import DocumentReady
from bokeh.layouts import column, row

# Import exposure time calculator
from ETC import exposure_time_calculator
from numpy import linspace
from astropy import units as u
import pdb


# Function definitions go here

def update_results():
    # Since == fails due to rounding errors, find closest value, i.e. ~=
    if etc.target == 'signal_noise_ratio':
        results.data = {
            'wavelengths': list(etc.wavelengths.to(u.nm).value) * len(etc.exposure),
            'exposure': [x for exp in etc.exposure.to(u.s).value for x in [exp]*len(etc.wavelengths)],
            'source': etc.source_count.flatten().value,
            'background': etc.background_count.flatten().value,
            'read_noise': [x for rnc in etc.read_noise_count.value for x in [rnc]*len(etc.wavelengths)],
            'dark_current': [x for dcc in etc.dark_current_count.value for x in [dcc]*len(etc.wavelengths)],
            'snr': etc.signal_noise_ratio.flatten().value,
            'exposure_slider': [False] * len(etc.wavelengths) * len(etc.exposure)
        }



class quantity_input:

    def value_callback(self, attr, old, new):
        if self.value_callback_active:
            try:
                parameter = new if len(self.contents.children) < 2 else str(new) + self.contents.children[1].value
                etc.set_parameter(self.key, parameter)
            except ValueError:
                if self.js_callback is not None:
                    self.contents.children[0].tags = ['js_callback_tag_true'] if self.contents.children[0].tags == ['js_callback_tag_false'] else [
                        'js_callback_tag_false']
                self.contents.children[0].value = old
            update_results()

    def unit_callback(self, attr, old, new):
        self.value_callback_active = False
        unit_old = u.ABmag if old == 'mag(AB)' else (
            u.STmag if old == 'mag(ST)' else (u.m_bol if old == 'mag(Bol)' else u.Unit(old)))
        unit_new = u.ABmag if new == 'mag(AB)' else (
            u.STmag if new == 'mag(ST)' else (u.m_bol if new == 'mag(Bol)' else u.Unit(new)))
        self.contents.children[0].value = (self.contents.children[0].value * unit_old).to(unit_new, equivalencies=self.equivalency).value
        self.contents.children[0].step = (self.contents.children[0].step * unit_old).to(unit_new, equivalencies=self.equivalency).value
        self.value_callback_active = True

    def __init__(self, key, name, default, unit_options=None, unit_default=None, js_callback=None, increment=1.0, low=None, high=None, equivalency=None, width=300):
        self.value_callback_active = True
        self.key = key
        self.name = name
        self.default = default
        self.unit_options = unit_options
        self.unit_default = unit_default
        self.js_callback = js_callback
        self.increment = increment
        self.low = low
        self.high = high
        self.equivalency = equivalency

        # Define value (and optional unit) inputs, add to self.contents
        self.contents = row(Spinner(title=self.name, value=self.default, step=self.increment, low=self.low, high=self.high, width=width, sizing_mode='stretch_width'), sizing_mode='stretch_width')
        self.contents.children[0].on_change('value', self.value_callback)
        if js_callback is not None:
           self.contents.children[0].js_on_change('tags', js_callback)
        if unit_options is not None and unit_default is not None:
            self.contents.children[0].width = int(width/2)
            self.contents.children.append(Select(title='\u00A0', value=unit_default, options=unit_options, width=int(width/2), sizing_mode='stretch_width'))
            self.contents.children[1].on_change('value', self.unit_callback)


class dropdown_input:

    def dropdown_callback(self, attr, old, new):
        etc.set_parameter(self.key, new)
        update_results()

    def __init__(self, key, name, default, options, width=300):
        self.key = key
        self.name = name
        self.default = default
        self.options = options

        self.contents = row(Select(title=self.name, value=self.default, options=self.options, width=width, sizing_mode='stretch_width'), sizing_mode='stretch_width')
        self.contents.children[0].on_change('value', self.dropdown_callback)


class exposure_panel:

    def callback(self, attr, old, new):
        if self.exposure_callback_active:
            if self._exposure_max.value < self._exposure_min.value:  # Can't have a negative range
                self._exposure_max.value = self._exposure_min.value
            exposure_list = linspace(self._exposure_min.value, self._exposure_max.value, 100) if self._exposure_max.value > self._exposure_min.value else [self._exposure_min.value]# 100 is Hard-coded for now, change later!!
            etc.set_parameter('exposure', [str(exp)+self._units.value for exp in exposure_list])
            update_results()
            res.reload()

    def unit_callback(self, attr, old, new):
        self.exposure_callback_active = False
        self._exposure_min.value = (self._exposure_min.value * u.Unit(old)).to(new).value
        self._exposure_max.value = (self._exposure_max.value * u.Unit(old)).to(new).value
        self.exposure_callback_active = True

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol']), name='exposure_panel', sizing_mode='stretch_width')

    def load(self):
        self._exposure_label = Paragraph(text='Exposure:', margin=(5, 5, 0, 5))
        self._exposure_min = Spinner(title='Min:', value=etc.exposure[0].value, low=0, width=100, sizing_mode='stretch_width')
        self._exposure_max = Spinner(title='Max:', value=etc.exposure[-1].value, low=0, width=100, sizing_mode='stretch_width')
        self._units = Select(title='\u00A0', value=str(etc.exposure.unit), options=['ms', 's', 'min', 'hr'], width=100, sizing_mode='stretch_width')
        self.exposure_callback_active = True
        self._exposure_min.on_change('value', self.callback)
        self._exposure_max.on_change('value', self.callback)
        self._units.on_change('value', self.unit_callback)

        self.contents.children = [self._exposure_label, row(self._exposure_min, self._exposure_max, self._units, sizing_mode='stretch_width')]


class source_panel:

    def file_callback(self, attr, old, new):
        etc.source.add_template(self._upload.children[1].value, self._upload.children[1].filename)

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol'], sizing_mode='stretch_width'), name='source_panel', sizing_mode='stretch_width')

    def load(self):
        self._types = dropdown_input('source.type', 'Source Type:', etc.source.type, etc.source.available_types)
        self._types.contents.children[0].on_change('value', lambda attr, old, new: self.set_content_visibility())  # Add callback to change inputs when source changes
        self._band = dropdown_input('source.wavelength_band', 'Band:', etc.source.wavelength_band,
                              list(vars(etc.source.config.wavelength_bands).keys()), width=100)
        self._brightness = quantity_input(
            key='source.brightness',
            name='Brightness:',
            default=etc.source.brightness.value,
            unit_options=['mag(AB)', 'mag(ST)', 'Jy', 'erg / (Angstrom cm2 s)'],
            unit_default=str(etc.source.brightness.unit),
            equivalency=u.spectral_density(u.Quantity(vars(etc.source.config.wavelength_bands)[self._band.contents.children[0].value])),
            width=200
        )
        # Add wavelength_band to brightness_row for sizing purposes
        self._brightness.contents.children.append(self._band.contents)
        # Define other inputs...
        self._redshift = quantity_input('source.redshift', 'Redshift:', etc.source.redshift.value)
        self._fwhm = quantity_input('source.fwhm', 'FWHM:', etc.source.fwhm.value, ['Angstrom', 'nm', 'um', 'mm'], str(etc.source.fwhm.unit), low=0)
        # To include options for fahrenheit and rankine, need 'u.imperial.enable()' in here and ETC.py... check w/ Sherry!
        self._temperature = quantity_input('source.temperature', 'Temperature:', etc.source.temperature.value, ['K', 'deg_C'], str(etc.source.temperature.unit), equivalency=u.temperature())
        self._index = quantity_input('source.index', 'Power Index:', etc.source.index.value)
        self._upload = column(
            Paragraph(text='Upload spectrum (ECSV):', margin=(5, 5, 0, 5), width=200, sizing_mode='stretch_width'),
            FileInput(accept='.txt', multiple=False, width=200, sizing_mode='stretch_width'),
            sizing_mode='stretch_width'
        )
        self._upload.children[1].on_change('filename', self.file_callback)
        self.contents.children = [
            self._types.contents,
            self._brightness.contents,
            self._redshift.contents,
            self._fwhm.contents,
            self._temperature.contents,
            self._index.contents,
            self._upload
        ]
        self.set_content_visibility()

    def set_content_visibility(self):
        # TODO -- ask Sherry about mag vs. temp, etc...
        content_map = {
            'type': self._types.contents,
            'brightness': self._brightness.contents,
            'redshift': self._redshift.contents,
            'fwhm': self._fwhm.contents,
            'temperature': self._temperature.contents,
            'index': self._index.contents
        }
        self.contents.children = []
        self.contents.children = ([value for key, value in content_map.items() if key in etc.source.active_parameters] + [self._upload])


class atmosphere_panel:

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol'], sizing_mode='stretch_width'), name='atmosphere_panel', sizing_mode='stretch_width', css_classes=['input_section'])

    def load(self):
        js_callback_code = """alert(name+' requires a value between '+min+' and '+max+' '+units);"""
        self._airmass_callback = CustomJS(args=dict(name='Airmass', min=etc.atmosphere._airmass_index[0].value,
                                              max=etc.atmosphere._airmass_index[-1].value,
                                              units=str(etc.atmosphere.airmass.unit)),
                                    code=js_callback_code)
        self._water_vapor_callback = CustomJS(args=dict(name='Water vapor', min=etc.atmosphere._water_vapor_index[0].value,
                                                  max=etc.atmosphere._water_vapor_index[-1].value,
                                                  units=str(etc.atmosphere.water_vapor.unit)), code=js_callback_code)

        self._seeing = quantity_input('atmosphere.seeing', 'Seeing:', etc.atmosphere.seeing.value, ['arcsec', 'arcmin'], str(etc.atmosphere.seeing.unit), increment=0.1, low=0)
        self._airmass = quantity_input('atmosphere.airmass', 'Airmass:', etc.atmosphere.airmass.value, js_callback=self._airmass_callback, increment=0.1)
        self._water_vapor = quantity_input('atmosphere.water_vapor', 'Water Vapor:', etc.atmosphere.water_vapor.value, ['um', 'mm', 'cm', 'm'], str(etc.atmosphere.water_vapor.unit), js_callback=self._water_vapor_callback, increment=0.5)

        self.contents.children = [self._seeing.contents, self._airmass.contents, self._water_vapor.contents]


class results_panel:
    # TODO -- Separate into individual graphs / sections!!

    def __init__(self):
        self.contents = row(Div(css_classes=['loading-symbol']), sizing_mode='scale_both', name='results')

    def load(self):
        # Plot 1
        step_size = (etc.exposure[1] - etc.exposure[0]).value if len(etc.exposure) > 1 else 0
        self._exposure_slider = Slider(start=etc.exposure[0].value, end=etc.exposure[-1].value, step=step_size, value=etc.exposure[0].value, title='Exposure ['+str(etc.exposure.unit)+']', syncable=False) if len(etc.exposure) > 1 else Slider(start=0, end=1, step=1, value=0, visible=False)
        #self._exposure_slider.on_change('value', lambda attr, old, new: update_results())
        js_code = """
            const exp_value = source.data['exposure'].reduce((prev, cur) => Math.abs(cur - slider.value) < Math.abs(prev - slider.value) ? cur : prev);
            return source.data['exposure'].map(x => x == exp_value);
        """
        self._exposure_view = CDSView(source=results, filters=[CustomJSFilter(args={'slider': self._exposure_slider}, code=js_code)])
        # ABOVE works perfectly, but doesn't run unless source or filters change -- below is supposed to change them, but gives weird errors...
        # HOW TO HANDLE THIS CLIENT_SIDE?????!?!?!?!?!?!?!!?!?
        self._exposure_slider.js_on_change('value', CustomJS(args=dict(view=self._exposure_view), code='const filters=view.filters;console.log(view);view.filters=[];console.log(view);view.filters=filters;'))
        self._snr_plot = figure(title='SNR', tools='pan, wheel_zoom, hover, reset, save', active_scroll='wheel_zoom',
               tooltips=[('S/N', '$y{0}'), ('λ (μm)', '$x{0}')], width=400, height=300)
        self._snr_plot.xaxis.axis_label = 'wavelengths (nm)'
        self._snr_plot.yaxis.axis_label = 'signal to noise ratio'
        self._snr_plot.line(x='wavelengths', y='snr', source=results, view=self._exposure_view)
        self._snr_plot.output_backend = 'svg'
        # Plot 2
        self._wavelength_slider = Slider(start=etc.wavelengths[0].value, end=etc.wavelengths[-1].value, step=(etc.wavelengths[1]-etc.wavelengths[0]).value, value=etc.wavelengths[0].value, title='Wavelength ['+str(etc.wavelengths.unit)+']', syncable=False)
        #self._wavelength_slider.on_change('value', lambda attr, old, new: update_results())


        self.contents.children = [column(self._snr_plot, self._exposure_slider)]

    def reload(self):
        # TODO -- display slider in chosen units from exposure_panel
        if len(etc.exposure) > 1:
            self._exposure_slider.title = 'Exposure [s]'
            self._exposure_slider.start = etc.exposure[0].to(u.s).value
            self._exposure_slider.end = etc.exposure[-1].to(u.s).value
            self._exposure_slider.step = (etc.exposure[1].to(u.s) - etc.exposure[0].to(u.s)).value
            # Trim value to be within new boundaries
            if self._exposure_slider.value < self._exposure_slider.start:
                self._exposure_slider.value = self._exposure_slider.start
            if self._exposure_slider.value > self._exposure_slider.end:
                self._exposure_slider.value = self._exposure_slider.end
            self._exposure_slider.visible = True
        else:
            self._exposure_slider.visible = False


class instrument_menu:

    def __init__(self):
        self.contents = Tabs(tabs=[], name='instruments')

    def load(self):
        self.contents.tabs = [ Panel(child=Div(), title=instrument.upper()) for instrument in etc.config.instruments ]
        self.contents.on_change('active', lambda attr, old, new: etc.set_parameter('instrument.name', etc.config.instruments[new]))



# Main code goes here




# START INITIALIZATION HERE
global etc
etc = None
results = ColumnDataSource(syncable=False)
instr = instrument_menu()
exp = exposure_panel()
atm = atmosphere_panel()
src = source_panel()  # TODO -- fix self-callback
res = results_panel()  # TODO -- call results.reload(), does it work?
curdoc().add_root(res.contents)
curdoc().add_root(instr.contents)
curdoc().add_root(exp.contents)
curdoc().add_root(atm.contents)
curdoc().add_root(src.contents)


def load_contents(event):
    global etc
    if etc is None:
        etc = exposure_time_calculator()
        update_results()
        instr.load()
        res.load()
        exp.load()
        src.load()
        atm.load()

curdoc().on_event(DocumentReady, load_contents)

