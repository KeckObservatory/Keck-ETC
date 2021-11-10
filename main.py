
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Panel, Select, Tabs, Spinner, Div, FileInput, Paragraph, CustomJS, Slider, Range1d
from bokeh.events import DocumentReady
from bokeh.layouts import column, row

# Import exposure time calculator
from ETC import exposure_time_calculator
from numpy import nanpercentile
from astropy import units as u
import pdb


# Function definitions go here

def update_results():
    if etc.target == 'signal_noise_ratio':
        """Below code is for computing multiple exposures...
        results.data = {
            'wavelengths': list(etc.wavelengths.to(u.nm).value) * len(etc.exposure),
            'exposure': [x for exp in etc.exposure.to(u.s).value for x in [exp]*len(etc.wavelengths)],
            'source': etc.source_count.flatten().value,
            'background': etc.background_count.flatten().value,
            'read_noise': [x for rnc in etc.read_noise_count.value for x in [rnc]*len(etc.wavelengths)],
            'dark_current': [x for dcc in etc.dark_current_count.value for x in [dcc]*len(etc.wavelengths)],
            'snr': etc.signal_noise_ratio.flatten().value
        }
        """
        # FOR SINGLE EXPOSURE, ASSUMED TO BE FIRST EXPOSURE...
        results.data = {
            'wavelengths': etc.wavelengths.to(u.nm).value,
            'exposure': [etc.exposure[0].to(u.s).value] * len(etc.wavelengths),
            'source': etc.source_count[0].value,
            'background': etc.background_count[0].value,
            'read_noise': [etc.read_noise_count.value] * len(etc.wavelengths),
            'dark_current': [etc.dark_current_count.value] * len(etc.wavelengths),
            'snr': etc.signal_noise_ratio[0].value
        }


    elif etc.target == 'exposure':
        results.data = {
            'wavelengths': etc.wavelengths.to(u.nm).value,
            'snr': [etc.signal_noise_ratio[0].value] * len(etc.wavelengths),
            'exposure': etc.exposure[0].to(u.s).value
        }
    summary.load()



class quantity_input:

    def value_callback(self, attr, old, new):
        if new is None:
            self.contents.children[0].value = old
        elif self.value_callback_active:
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
        self.contents = row(Spinner(title=self.name, value=self.default, step=self.increment, low=self.low, high=self.high, width=width, sizing_mode='scale_width'), sizing_mode='scale_width')
        self.contents.children[0].on_change('value_throttled', self.value_callback)
        if js_callback is not None:
           self.contents.children[0].js_on_change('tags', js_callback)
        if unit_options is not None and unit_default is not None:
            self.contents.children[0].width = int(width/2)
            self.contents.children.append(Select(title='\u00A0', value=unit_default, options=unit_options, width=int(width/2), sizing_mode='scale_width'))
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

        self.contents = row(Select(title=self.name, value=self.default, options=self.options, width=width, sizing_mode='scale_width'), sizing_mode='scale_width')
        self.contents.children[0].on_change('value', self.dropdown_callback)


class exposure_panel:

    def exposure_callback(self, attr, old, new):
        if self.target.value == 'signal to noise ratio':
            if self.exposure_min.value is None:
                self.exposure_min.value = old
            elif self.exposure_max.value is None:
                self.exposure_max.value = old
            elif self.exposure_active_flag:
                if self.exposure_max.value < self.exposure_min.value:  # Can't have a negative range
                    self.exposure_max.value = self.exposure_min.value
                res.reload()
        elif self.target.value == 'exposure':
            if self.snr_min.value is None:
                self.snr_min.value = old
            elif self.snr_max.value is None:
                self.snr_max.value = old
            else:
                if self.snr_max.value < self.snr_min.value:
                    self.snr_max.value = self.snr_min.value
                res.reload()

    def unit_callback(self, attr, old, new):
        self.exposure_active_flag = False
        self.exposure_min.value = (self.exposure_min.value * u.Unit(old)).to(new).value
        self.exposure_max.value = (self.exposure_max.value * u.Unit(old)).to(new).value
        res.exposure_slider.value = (res.exposure_slider.value * u.Unit(old)).to(new).value
        summary.load()
        self.exposure_active_flag = True

    def target_callback(self, attr, old, new):
        if new == 'exposure':
            etc.set_parameter('signal_noise_ratio', etc.config.defaults.signal_noise_ratio)
            self.snr_min.value = etc.signal_noise_ratio[0].value
            self.snr_max.value = etc.signal_noise_ratio[-1].value
            self.contents.children = [self.title.contents, self.target, self.snr_label, row(self.snr_min, self.snr_max, sizing_mode='scale_width')]
        if new == 'signal to noise ratio':
            etc.set_parameter('exposure', etc.config.defaults.exposure)
            self.exposure_min.value = etc.exposure[0].value
            self.exposure_max.value = etc.exposure[-1].value
            self.contents.children = [self.title.contents, self.target, self.exposure_label, row(self.exposure_min, self.exposure_max, self.units, sizing_mode='scale_width')]
        update_results()
        res.reload()


    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol']), name='exposure_panel', sizing_mode='scale_width', css_classes=['input_section'])

    def load(self):
        self.exposure_active_flag = True
        self.title = section_title('Exposure')
        self.exposure_label = Paragraph(text='Exposure:', margin=(5, 5, 0, 5))
        self.exposure_min = Spinner(title='Min:', value=etc.exposure[0].value, low=0, width=100, sizing_mode='scale_width')
        self.exposure_max = Spinner(title='Max:', value=etc.exposure[-1].value, low=0, width=100, sizing_mode='scale_width')
        self.units = Select(title='\u00A0', value=str(etc.exposure.unit), options=['ms', 's', 'min', 'hr'], width=100, sizing_mode='scale_width')
        self.exposure_min.on_change('value_throttled', self.exposure_callback)
        self.exposure_max.on_change('value_throttled', self.exposure_callback)
        self.units.on_change('value', self.unit_callback)

        # Create dropdown for selecting whether to calculate snr or exp
        self.target = Select(title='Calculation Target:', value='signal to noise ratio', options=['signal to noise ratio', 'exposure'], width=300, sizing_mode='scale_width')
        self.target.on_change('value', self.target_callback)
        # Create elements to calculate snr
        self.snr_label = Paragraph(text='Signal to Noise Ratio:', margin=(5, 5, 0, 5))
        self.snr_min = Spinner(title='Min:', value=0, low=0, width=100, sizing_mode='scale_width')  # Default to 0 because exp is initially active
        self.snr_max = Spinner(title='Max:', value=0, low=0, width=100, sizing_mode='scale_width')
        self.snr_min.on_change('value_throttled', self.exposure_callback)
        self.snr_max.on_change('value_throttled', self.exposure_callback)

        self.contents.children = [self.title.contents, self.target, self.exposure_label, row(self.exposure_min, self.exposure_max, self.units, sizing_mode='scale_width')]


class source_panel:

    def file_callback(self, attr, old, new):
        # TODO -- support for FITS file formats
        etc.source.add_template(self.upload.children[1].value, self.upload.children[1].filename)
        self.set_content_visibility()

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol'], sizing_mode='scale_width'), name='source_panel', sizing_mode='scale_width', css_classes=['input_section'])

    def load(self):
        self.title = section_title('Source')

        self.types = dropdown_input('source.type', 'Source Type:', etc.source.type, etc.source.available_types)
        self.types.contents.children[0].on_change('value', lambda attr, old, new: self.set_content_visibility())  # Add callback to change inputs when source changes
        self.band = dropdown_input('source.wavelength_band', 'Band:', etc.source.wavelength_band,
                              list(vars(etc.source.config.wavelength_bands).keys()), width=100)
        self.brightness = quantity_input(
            key='source.brightness',
            name='Brightness:',
            default=etc.source.brightness.value,
            unit_options=['mag(AB)', 'mag(ST)', 'Jy', 'erg / (Angstrom cm2 s)'],
            unit_default=str(etc.source.brightness.unit),
            equivalency=u.spectral_density(u.Quantity(vars(etc.source.config.wavelength_bands)[self.band.contents.children[0].value])),
            width=200
        )
        # Add wavelength_band to brightness_row for sizing purposes
        self.brightness.contents.children.append(self.band.contents)
        # Define other inputs...
        self.redshift = quantity_input('source.redshift', 'Redshift:', etc.source.redshift.value)
        self.fwhm = quantity_input('source.fwhm', 'FWHM:', etc.source.fwhm.value, ['Angstrom', 'nm', 'um', 'mm'], str(etc.source.fwhm.unit), low=0)
        # To include options for fahrenheit and rankine, need 'u.imperial.enable()' in here and ETC.py... check w/ Sherry!
        self.temperature = quantity_input('source.temperature', 'Temperature:', etc.source.temperature.value, ['K', 'deg_C'], str(etc.source.temperature.unit), equivalency=u.temperature())
        self.index = quantity_input('source.index', 'Power Index:', etc.source.index.value)
        self.upload = column(
            Paragraph(text='Upload spectrum (ECSV):', margin=(5, 5, 0, 5), width=200, sizing_mode='scale_width'),
            FileInput(accept='.txt', multiple=False, width=200, sizing_mode='scale_width'),
            sizing_mode='scale_width'
        )
        self.upload.children[1].on_change('filename', self.file_callback)
        self.upload.children[1].js_on_change('value', CustomJS(args={}, code='console.log(cb_obj);'))
        self.contents.children = [
            self.title.contents,
            self.types.contents,
            self.brightness.contents,
            self.redshift.contents,
            self.fwhm.contents,
            self.temperature.contents,
            self.index.contents,
            self.upload
        ]
        self.set_content_visibility()

    def set_content_visibility(self):
        # TODO -- ask Sherry about mag vs. temp, etc...
        content_map = {
            'type': self.types.contents,
            'brightness': self.brightness.contents,
            'redshift': self.redshift.contents,
            'fwhm': self.fwhm.contents,
            'temperature': self.temperature.contents,
            'index': self.index.contents
        }
        new_contents = [self.title.contents] + [value for key, value in content_map.items() if key in etc.source.active_parameters] + [self.upload]
        # In order to size properly, first set to []
        self.contents.children = [self.upload]
        self.contents.children = new_contents


class atmosphere_panel:

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol'], sizing_mode='scale_width'), name='atmosphere_panel', sizing_mode='scale_width', css_classes=['input_section'])

    def load(self):
        self.title = section_title('Atmosphere')
        js_callback_code = """alert(name+' requires a value between '+min+' and '+max+' '+units);"""
        self.airmass_callback = CustomJS(args=dict(name='Airmass', min=etc.atmosphere._airmass_index[0].value,
                                              max=etc.atmosphere._airmass_index[-1].value,
                                              units=str(etc.atmosphere.airmass.unit)),
                                    code=js_callback_code)
        self.water_vapor_callback = CustomJS(args=dict(name='Water vapor', min=etc.atmosphere._water_vapor_index[0].value,
                                                  max=etc.atmosphere._water_vapor_index[-1].value,
                                                  units=str(etc.atmosphere.water_vapor.unit)), code=js_callback_code)

        self.seeing = quantity_input('atmosphere.seeing', 'Seeing:', etc.atmosphere.seeing.value, ['arcsec'], str(etc.atmosphere.seeing.unit), increment=0.1, low=0)
        self.airmass = quantity_input('atmosphere.airmass', 'Airmass:', etc.atmosphere.airmass.value, js_callback=self.airmass_callback, increment=0.1)
        self.water_vapor = quantity_input('atmosphere.water_vapor', 'Water Vapor:', etc.atmosphere.water_vapor.value, ['mm', 'cm'], str(etc.atmosphere.water_vapor.unit), js_callback=self.water_vapor_callback, increment=0.5)

        self.contents.children = [self.title.contents, self.seeing.contents, self.airmass.contents, self.water_vapor.contents]


class section_title:

    def __init__(self, text):
        self.contents = column(Paragraph(text=text, margin=(5,5,0,5), sizing_mode='scale_width', css_classes=['section-title']), Div(css_classes=['hrule'], sizing_mode='scale_width'), sizing_mode='scale_width', margin=(0,0,-10,0), css_classes=['input_section'])


class big_number:

    def __init__(self, big, small):
        self.contents = column(Paragraph(text=big, css_classes=['sidebar-big', 'center']), Paragraph(text=small, css_classes=['sidebar-small', 'center']), Div(css_classes=['hrule', 'center'], sizing_mode='scale_width'), css_classes=['center'], sizing_mode='scale_width')



class summary_panel:
    # TODO -- Add everything, make it look good, etc.

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol']), sizing_mode='scale_width', name='sidebar', css_classes=['input_section'])

    def load(self):
        # Quick ~hacky check to make sure everything else is loaded first, switch to boolean flag for clarity later
        if len(atm.contents.children) > 1:
            central_wavelength = u.Quantity(
                vars(etc.source.config.wavelength_bands)[src.band.contents.children[0].value])
            wavelength_index = abs(etc.wavelengths - central_wavelength.to(etc.wavelengths.unit)) == min(
                abs(etc.wavelengths - central_wavelength.to(etc.wavelengths.unit)))
            self.title = section_title(etc.instrument.name.upper())
            self.flux_label = big_number(
                f'{etc.source_flux[wavelength_index][0].to("erg / (cm^2 s Angstrom)", equivalencies=u.spectral_density(central_wavelength)).value:.1} flam',
                'source flux')
            self.wav_label = big_number(f'{central_wavelength.to(u.um).value:.4} μm', 'central wavelength')
            self.clk_label = big_number('--- s', 'clock time')
            if etc.target == 'signal_noise_ratio':
                self.exp_label = big_number(f'{float(res.exposure_slider.value):.3} {exp.units.value}', 'exposure')
                self.snr_label = big_number(f'{etc.signal_noise_ratio[0][wavelength_index][0]:.4}', 'S/N')
            elif etc.target == 'exposure':
                self.exp_label = big_number(f'{etc.exposure[0][wavelength_index][0].value:.3} {etc.exposure[0][wavelength_index][0].unit}', 'exposure')
                self.snr_label = big_number(f'{float(res.snr_slider.value):.4}', 'S/N')
            self.contents.children = [self.title.contents, column(self.exp_label.contents, self.snr_label.contents,
                                                                      self.wav_label.contents, self.flux_label.contents,
                                                                      self.clk_label.contents,
                                                                      css_classes=['sidebar-container'])]


class results_panel:
    # TODO -- Separate into individual graphs / sections!!

    def slider_callback(self, attr, old, new):
        if exp.target.value == 'signal to noise ratio':
            etc.set_parameter('exposure', [str(new)+exp.units.value])
        elif exp.target.value == 'exposure':
            etc.set_parameter('signal_noise_ratio', [new])
        update_results()

    def __init__(self):
        self.contents = row(Div(css_classes=['loading-symbol']), sizing_mode='scale_width', name='results', css_classes=['input_section'])

    def load(self):
        # Plot 1
        step_size = (etc.exposure[1] - etc.exposure[0]).value if len(etc.exposure) > 1 else 0
        self.exposure_slider = Slider(start=etc.exposure[0].value, end=etc.exposure[-1].value, step=step_size, value=etc.exposure[0].value, title='Exposure ['+str(etc.exposure.unit)+']', syncable=False) if len(etc.exposure) > 1 else Slider(start=etc.exposure[0].value, end=etc.exposure[0].value+1, step=1, value=etc.exposure[0].value, visible=False)
        self.exposure_slider.on_change('value_throttled', self.slider_callback)
        self.snr_slider = Slider(start=0, end=1, value=0, step=1, title='Signal to Noise Ratio')
        self.snr_slider.on_change('value_throttled', self.slider_callback)
        """ FOR CLIENT-SIDE COMPUTATION
        js_code = \"""
            const exp_value = source.data['exposure'].reduce((prev, cur) => Math.abs(cur - cb_obj.value) < Math.abs(prev - cb_obj.value) ? cur : prev);
            filter.booleans = source.data['exposure'].map(x => x == exp_value);
            source.change.emit();
        \"""
        self.exposure_filter = BooleanFilter(booleans=[False] * len(results.data['exposure']))
        self.exposure_view = CDSView(source=results, filters=[self.exposure_filter])
        # Callback to change filter, but currently plot is blank... why?
        self.exposure_slider.js_on_change('value', CustomJS(args=dict(source=results, filter=self.exposure_filter), code=js_code))
        """

        # Plot snr vs. wavelength
        self.snr_plot = figure(title='Signal to Noise Ratio', tools='pan, wheel_zoom, hover, reset, save', active_scroll='wheel_zoom',
               tooltips=[('S/N', '$y{0}'), ('λ (μm)', '$x{0.000}')], width=400, height=300)
        self.snr_plot.xaxis.axis_label = 'wavelengths (nm)'
        self.snr_plot.yaxis.axis_label = 'signal to noise ratio'
        self.snr_plot.scatter(x='wavelengths', y='snr', source=results, alpha=0.5, size=6)  # , view=self.exposure_view
        self.snr_plot.line(x='wavelengths', y='snr', source=results)
        self.snr_plot.output_backend = 'svg'

        # Plot exp vs. wavelength
        self.exp_plot = figure(title='Exposure Time', tools='pan, wheel_zoom, hover, reset, save', active_scroll='wheel_zoom',
               tooltips=[('exp (s)', '$y{0}'), ('λ (μm)', '$x{0.000}')], width=400, height=300)
        self.exp_plot.xaxis.axis_label = 'wavelengths (nm)'
        self.exp_plot.yaxis.axis_label = 'exposure time (s)'
        self.exp_plot.scatter(x='wavelengths', y='exposure', source=results, alpha=0.5, size=6)  # , view=self.exposure_view
        self.exp_plot.line(x='wavelengths', y='exposure', source=results)
        self.exp_plot.output_backend = 'svg'


        # Plot 2
        self.wavelength_slider = Slider(start=etc.wavelengths[0].value, end=etc.wavelengths[-1].value, step=(etc.wavelengths[1]-etc.wavelengths[0]).value, value=etc.wavelengths[0].value, title='Wavelength ['+str(etc.wavelengths.unit)+']', syncable=False)
        

        
        self.exposure_slider.value = self.exposure_slider.value
        self.contents.children = [column(self.snr_plot, self.exposure_slider)]

    def reload(self):
        if exp.target.value == 'signal to noise ratio':
            if exp.exposure_max.value > exp.exposure_min.value:
                self.exposure_slider.title = 'Exposure ['+exp.units.value+']'
                self.exposure_slider.start = exp.exposure_min.value
                self.exposure_slider.end = exp.exposure_max.value
                self.exposure_slider.step = (self.exposure_slider.end - self.exposure_slider.start) / 100  # HARD-CODED FOR NOW, CHANGE LATER??
                # Trim current value to be within new boundaries, if applicable
                if self.exposure_slider.value < self.exposure_slider.start:
                    self.exposure_slider.value = self.exposure_slider.start
                if self.exposure_slider.value > self.exposure_slider.end:
                    self.exposure_slider.value = self.exposure_slider.end
                self.exposure_slider.visible = True
            else:
                self.exposure_slider.visible = False
            if self.exposure_slider not in self.contents.children[0].children:
                self.contents.children = [column(self.snr_plot, self.exposure_slider)]
        elif exp.target.value == 'exposure':
            if exp.snr_max.value > exp.snr_min.value:
                self.snr_slider.start = exp.snr_min.value
                self.snr_slider.end = exp.snr_max.value
                self.snr_slider.step = (self.snr_slider.end - self.snr_slider.start) / 100  # HARD-CODED FOR NOW, CHANGE LATER??
                # Trim current value to be within new boundaries, if applicable
                if self.snr_slider.value < self.snr_slider.start:
                    self.snr_slider.value = self.snr_slider.start
                if self.snr_slider.value > self.snr_slider.end:
                    self.snr_slider.value = self.snr_slider.end
                self.snr_slider.visible = True
            else:
                self.snr_slider.visible = False
            if self.snr_slider not in self.contents.children[0].children:
                self.contents.children = [column(self.exp_plot, self.snr_slider)]
                # Set y axis range to be more helpful than default
                self.exp_plot.y_range.start = min(results.data['exposure'])*.8
                self.exp_plot.y_range.end = nanpercentile(results.data['exposure'], 50)

class instrument_menu:

    def callback(self, attr, old, new):
        etc.set_parameter('instrument.name', etc.config.instruments[new])
        update_results()

    def __init__(self):
        self.contents = Tabs(tabs=[], name='instruments', sizing_mode='scale_width')

    def load(self):
        # Set correct tab active, before defining tabs because it looks better as it loads
        self.contents.active = [i for i, x in enumerate(etc.config.instruments) if x.lower() == etc.instrument.name.lower()][0]
        self.contents.tabs = [ Panel(child=Div(sizing_mode='scale_width'), title=instrument.upper()) for instrument in etc.config.instruments ]
        self.contents.on_change('active', self.callback)



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
summary = summary_panel()
curdoc().add_root(res.contents)
curdoc().add_root(instr.contents)
curdoc().add_root(exp.contents)
curdoc().add_root(atm.contents)
curdoc().add_root(src.contents)
curdoc().add_root(summary.contents)


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
        summary.load()

curdoc().on_event(DocumentReady, load_contents)

