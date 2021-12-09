
from bokeh.io import curdoc
from bokeh.plotting import figure, gridplot
from bokeh.models import ColumnDataSource, Panel, Select, Tabs, Spinner, Div, FileInput, Paragraph, CustomJS, Slider, Span, Button, Label, BoxAnnotation
from bokeh.events import DocumentReady, Reset, MouseMove, Tap
from bokeh.layouts import column, row

# Import exposure time calculator
import yaml
from calculator.ETC import exposure_time_calculator
from numpy import nanpercentile, linspace, round, isnan
from pathlib import Path
from astropy import units as u
from urllib.parse import urlparse
from re import sub
import pdb


# Function definitions go here

def update_results():

    if etc.target == 'signal_noise_ratio':
        # FOR SINGLE EXPOSURE, ASSUMED TO BE FIRST EXPOSURE...
        results.data = {
            'wavelengths': etc.wavelengths.to(u.nm).value,
            'exposure': [etc.exposure[0].to(u.s).value] * len(etc.wavelengths),
            'source': [x if x > 1 else 1 for x in etc.source_count_adu[0].value],  # Log plot, so remove the zeros!
            'background': [x if x > 1 else 1 for x in etc.background_count_adu[0].value],  # Log plot, so remove the zeros!
            'read_noise': list(etc.read_noise_count_adu.value) * len(etc.wavelengths),
            'dark_current': list(etc.dark_current_count_adu.value) * len(etc.wavelengths),
            'snr': etc.signal_noise_ratio[0].value,
            'nonlinear':[etc.instrument.nonlinear_depth.value] * len(etc.wavelengths),
            'integration': [etc.integration_time.to(u.s)[0].value] * len(etc.wavelengths),
            'flux': etc.source_flux.to(u.erg / (u.Angstrom * u.cm**2 * u.s), equivalencies=u.spectral_density(etc.wavelengths)).value
        }

    elif etc.target == 'exposure':
        results.data = {
            'wavelengths': etc.wavelengths.to(u.nm).value,
            'snr': [etc.signal_noise_ratio[0].value] * len(etc.wavelengths),
            'exposure': etc.exposure[0].to(u.s).value,
            'source': [x if x > 1 else 1 for x in etc.source_count_adu[0].value],  # Log plot, so remove the zeros!
            'background': [x if x > 1 else 1 for x in etc.background_count_adu[0].value],  # Log plot, so remove the zeros!
            'read_noise': etc.read_noise_count_adu[0].value,
            'dark_current': etc.dark_current_count_adu[0].value,
            'nonlinear': [etc.instrument.nonlinear_depth.value] * len(etc.wavelengths),
            'integration': etc.integration_time[0].to(u.s).value,
            'flux': etc.source_flux.to(u.erg / (u.Angstrom * u.cm**2 * u.s), equivalencies=u.spectral_density(etc.wavelengths)).value
        }


    js.set_cookies(etc.get_parameters())



class quantity_input:

    def value_callback(self, attr, old, new):
        if new is None:
            self.contents.children[0].value = old
        elif self.value_callback_active:
            try:
                parameter = new if len(self.contents.children) < 2 else str(new) + self.contents.children[1].value
                etc.set_parameter(self.key, parameter)
            except (RecursionError, ValueError) as e:
                if self.error_text is not None:
                    js.show_alert(self.error_text)
                else:
                    js.show_alert('Error: '+str(e))
                self.value_callback_active = False
                self.contents.children[0].value = old
                self.value_callback_active = True
            update_results()

    def unit_callback(self, attr, old, new):
        self.value_callback_active = False
        unit_old = u.ABmag if old == 'mag(AB)' else (
            u.STmag if old == 'mag(ST)' else (u.m_bol if old == 'mag(Bol)' else (etc.source.vegamag if old == 'mag(vega)' else u.Unit(old))))
        unit_mid = u.AB if unit_old==u.ABmag else (u.ST if unit_old==u.STmag else unit_old)
        unit_new = u.ABmag if new == 'mag(AB)' else (
            u.STmag if new == 'mag(ST)' else (u.m_bol if new == 'mag(Bol)'  else (etc.source.vegamag if new == 'mag(vega)' else u.Unit(new))))
        self.contents.children[0].value = (self.contents.children[0].value * unit_old).to(unit_mid).to(unit_new, equivalencies=self.equivalency).value
        if not(old in ['mag(AB)', 'mag(ST)', 'mag(Bol)', 'mag(vega)'] or new in ['mag(AB)', 'mag(ST)', 'mag(Bol)', 'mag(vega)']): # Don't do these conversions for magnitude
            self.contents.children[0].step = (self.contents.children[0].step * unit_old).to(unit_mid).to(unit_new, equivalencies=self.equivalency).value
        self.value_callback_active = True

    def __init__(self, key, name, default, unit_options=None, unit_default=None, error_text=None, increment=1.0, low=None, high=None, equivalency=None, width=300, css_classes=[]):
        self.value_callback_active = True
        self.key = key
        self.name = name
        self.default = default
        self.unit_options = unit_options
        self.unit_default = unit_default
        self.error_text = error_text
        self.increment = increment
        self.low = low
        self.high = high
        self.equivalency = equivalency
        self.css_classes = css_classes

        # Define value (and optional unit) inputs, add to self.contents
        self.contents = row(Spinner(title=self.name, value=self.default, step=self.increment, low=self.low, high=self.high, width=width, sizing_mode='scale_width'), sizing_mode='scale_width')
        self.contents.children[0].on_change('value', self.value_callback)
        if unit_options is not None and unit_default is not None:
            self.contents.children[0].width = int(width/2)
            self.contents.children.append(Select(title='\u00A0', value=unit_default, options=unit_options, width=int(width/2), sizing_mode='scale_width', css_classes=self.css_classes))
            self.contents.children[1].on_change('value', self.unit_callback)
        else:
            self.contents.children[0].css_classes = self.css_classes


class dropdown_input:

    def dropdown_callback(self, attr, old, new):
        etc.set_parameter(self.key, new)
        update_results()

    def __init__(self, key, name, default, options, width=300, css_classes=[]):
        self.key = key
        self.name = name
        self.default = default
        self.options = options

        self.contents = row(Select(title=self.name, value=self.default, options=self.options, width=width, sizing_mode='scale_width', css_classes=css_classes), sizing_mode='scale_width')
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
                elif self.exposure_max.value > self.exposure_min.value:
                    self.exposure_slider.title = 'Exposure ['+self.units.value+']'
                    self.exposure_slider.start = self.exposure_min.value
                    self.exposure_slider.end = self.exposure_max.value
                    self.exposure_slider.step = (self.exposure_slider.end - self.exposure_slider.start) / 100  # HARD-CODED FOR NOW, CHANGE LATER??
                    # Trim current value to be within new boundaries, if applicable
                    if self.exposure_slider.value < self.exposure_slider.start:
                        self.exposure_slider.value = self.exposure_slider.start
                    if self.exposure_slider.value > self.exposure_slider.end:
                        self.exposure_slider.value = self.exposure_slider.end
                res.reload()
        elif self.target.value == 'exposure':
            if self.snr_min.value is None:
                self.snr_min.value = old
            elif self.snr_max.value is None:
                self.snr_max.value = old
            else:
                if self.snr_max.value < self.snr_min.value:
                    self.snr_max.value = self.snr_min.value
                elif self.snr_max.value > self.snr_min.value:
                    self.snr_slider.start = self.snr_min.value
                    self.snr_slider.end = self.snr_max.value
                    self.snr_slider.step = (self.snr_slider.end - self.snr_slider.start) / 100  # HARD-CODED FOR NOW, CHANGE LATER??
                    # Trim current value to be within new boundaries, if applicable
                    if self.snr_slider.value < self.snr_slider.start:
                        self.snr_slider.value = self.snr_slider.start
                    if self.snr_slider.value > self.snr_slider.end:
                        self.snr_slider.value = self.snr_slider.end
                res.reload()

    def unit_callback(self, attr, old, new):
        self.exposure_active_flag = False
        self.exposure_min.value = (self.exposure_min.value * u.Unit(old)).to(new).value
        self.exposure_max.value = (self.exposure_max.value * u.Unit(old)).to(new).value
        self.exposure_slider.value = (self.exposure_slider.value * u.Unit(old)).to(new).value
        self.exposure_slider.title = 'Exposure ['+new+']'
        self.exposure_active_flag = True

    def slider_callback(self, attr, old, new):
        if self.target.value == 'signal to noise ratio':
            etc.set_parameter('exposure', [str(new)+self.units.value])
        elif self.target.value == 'exposure':
            etc.set_parameter('signal_noise_ratio', [new])
        update_results()

    def target_callback(self, attr, old, new):
        if new == 'exposure':
            new_contents = [self.snr if item==self.exposure else item for item in self.contents.children]
            self.contents.children = [Div(css_classes=['loading-symbol'])]
            etc.set_parameter('target', 'exposure')
            self.snr_min.value = 0
            self.snr_max.value = etc.signal_noise_ratio[0].value * 2
            self.snr_slider.value = etc.signal_noise_ratio[0].value
            self.contents.children = new_contents

        if new == 'signal to noise ratio':
            new_contents = [self.exposure if item==self.snr else item for item in self.contents.children]
            self.contents.children = [Div(css_classes=['loading-symbol'])]
            etc.set_parameter('target', 'signal_noise_ratio')
            self.exposure_min.value = 0
            self.exposure_max.value = etc.exposure[0].to(self.units.value).value * 2
            self.exposure_slider.value = etc.exposure[0].to(self.units.value).value
            self.contents.children = new_contents
        update_results()
        res.reload()


    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol']), name='exposure_panel', sizing_mode='scale_width', css_classes=['input_section'])

    def reset(self):
        self.contents.children = [Div(css_classes=['loading-symbol'])]

    def load(self):
        self.exposure_active_flag = True
        self.title = section_title('Exposure')
        self.exposure_min = Spinner(title='Min:', value=0, low=0, width=100, sizing_mode='scale_width')
        self.exposure_max = Spinner(title='Max:', value=1, low=0, width=100, sizing_mode='scale_width')
        self.units = Select(title='\u00A0', value=str(etc.exposure.unit), options=['ms', 's', 'min', 'hr'], width=100, sizing_mode='scale_width')
        self.exposure_slider = Slider(start=0, end=1, step=1, value=0, title='Exposure ['+str(etc.exposure.unit)+']', width=100, sizing_mode='scale_width', css_classes=['exposure_input'])
        if etc.target == 'signal_noise_ratio':
            self.exposure_max.value = etc.exposure[0].value * 2
            self.exposure_slider.end = self.exposure_max.value
            self.exposure_slider.step = self.exposure_max.value / 100
            self.exposure_slider.value = etc.exposure[0].value
        self.exposure_min.on_change('value', self.exposure_callback)
        self.exposure_max.on_change('value', self.exposure_callback)
        self.units.on_change('value', self.unit_callback)
        self.exposure_slider.on_change('value_throttled', self.slider_callback)
        self.exposure = column(self.exposure_slider, row(self.exposure_min, self.exposure_max, self.units, sizing_mode='scale_width'), sizing_mode='scale_width')

        # Create dropdown for selecting whether to calculate snr or exp
        self.target = Select(title='Calculation Target:', value='signal to noise ratio', options=['signal to noise ratio', 'exposure'], width=300, sizing_mode='scale_width', css_classes=['calculation_target'])
        if etc.target == 'exposure':
            self.target.value = 'exposure'
        self.target.on_change('value', self.target_callback)

        # Create elements to calculate snr
        self.snr_min = Spinner(title='Min:', value=0, low=0, width=100, sizing_mode='scale_width', step=5)
        self.snr_max = Spinner(title='Max:', value=1, low=0, width=100, sizing_mode='scale_width', step=5)
        self.snr_slider = Slider(start=0, end=1, value=0, step=1, title='Signal to Noise Ratio', width=100, sizing_mode='scale_width')
        if etc.target == 'exposure':
            self.snr_max.value = etc.signal_noise_ratio[0].value * 2
            self.snr_slider.end = self.snr_max.value
            self.snr_slider.step = self.snr_max.value / 100
            self.snr_slider.value = etc.signal_noise_ratio[0].value
        self.snr_min.on_change('value', self.exposure_callback)
        self.snr_max.on_change('value', self.exposure_callback)
        self.snr_slider.on_change('value_throttled', self.slider_callback)
        self.snr = column(self.snr_slider, row(self.snr_min, self.snr_max, sizing_mode='scale_width'), sizing_mode = 'scale_width')

        # Dithers
        self.dithers = quantity_input('dithers', 'Dithers:', etc.dithers.value, low=1, width=150)
        self.repeats = quantity_input('repeats', 'Repeats:', etc.repeats.value, low=1, width=150)
        self.coadds = quantity_input('coadds', 'Coadds:', etc.coadds.value, low=1, width=150)
        self.reads = dropdown_input('reads', 'Reads:', str(int(etc.reads.value)), [str(x) for x in etc.config.reads_options], width=150, css_classes=['reads_input'])
        
        if etc.target == 'signal_noise_ratio':
            self.contents.children = [
                self.title.contents,
                self.target,
                self.exposure,
                row(self.dithers.contents, self.repeats.contents, sizing_mode='scale_width'),
                row(self.coadds.contents, self.reads.contents, sizing_mode = 'scale_width')
            ]
        elif etc.target == 'exposure':
            self.contents.children = [
                self.title.contents, 
                self.target,
                self.snr,
                row(self.dithers.contents, self.repeats.contents, sizing_mode='scale_width'),
                row(self.coadds.contents, self.reads.contents, sizing_mode = 'scale_width')
            ]


class source_panel:

    def file_callback(self, attr, old, new):
        try:
            etc.source.add_template(self.upload.children[1].value, self.upload.children[1].filename)
        except:
            js.show_alert('Error: uploaded source spectrum is not valid')
            self.contents.children.remove(self.upload)  # Resets text label to "No file chosen"
        self.types.options =  [vars(etc.source.config.source_types)[source].name for source in etc.source.available_types]
        self.set_content_visibility()

    def type_callback(self, attr, old, new):
        name = [key for key, val in vars(etc.source.config.source_types).items() if val.name == new]
        etc.set_parameter('source.type', name[0])
        update_results()
        self.set_content_visibility()
        

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol'], sizing_mode='scale_width'), name='source_panel', sizing_mode='scale_width', css_classes=['input_section'])


    def reset(self):
        self.contents.children = [Div(css_classes=['loading-symbol'], sizing_mode='scale_width')]

    def load(self):
        self.title = section_title('Source')

        self.types = Select(title='Source Type:', value=vars(etc.source.config.source_types)[etc.source.type].name, options=[vars(etc.source.config.source_types)[source].name for source in etc.source.available_types], width=300, sizing_mode='scale_width')
        self.types.on_change('value', self.type_callback)
        
        self.band = dropdown_input('source.wavelength_band', 'Band:', etc.source.wavelength_band,
                              list(vars(etc.source.config.wavelength_bands).keys()), width=100)

        u.add_enabled_units([etc.source.flam, etc.source.photlam])

        self.brightness = quantity_input(
            key='source.brightness',
            name='Flux:',
            default=etc.source.brightness.value,
            unit_options=['mag(AB)', 'mag(vega)', 'mag(ST)', 'Jy', 'flam', 'photlam'],
            unit_default=str(etc.source.brightness.unit),
            equivalency=u.spectral_density(u.Quantity(vars(etc.source.config.wavelength_bands)[self.band.contents.children[0].value]))+
            etc.source.spectral_density_vega(u.Quantity(vars(etc.source.config.wavelength_bands)[self.band.contents.children[0].value])),
            width=200
        )
        # Add wavelength_band to brightness_row for sizing purposes
        self.brightness.contents.children.append(self.band.contents)

        # Define other inputs...
        self.redshift = quantity_input('source.redshift', 'Redshift:', etc.source.redshift.value)
        self.width = quantity_input('source.width', 'Line Width:', etc.source.width.value, ['Angstrom', 'nm', 'um', 'mm'], str(etc.source.width.unit), low=0)
        # To include options for fahrenheit and rankine, need 'u.imperial.enable()' in here and ETC.py... check w/ Sherry!
        self.temperature = quantity_input('source.temperature', 'Temperature:', etc.source.temperature.value, ['K', 'deg_C'], str(etc.source.temperature.unit), equivalency=u.temperature())
        self.index = quantity_input('source.index', 'Power Index:', etc.source.index.value)
        self.upload = column(
            Paragraph(text='Upload spectrum:', margin=(5, 5, 0, 5), width=200, sizing_mode='scale_width', css_classes=['file_upload']),
            FileInput(accept='.txt,.fits', multiple=False, width=200, sizing_mode='scale_width', css_classes=['file_upload']),
            sizing_mode='scale_width'
        )
        self.upload.children[1].on_change('filename', self.file_callback)
        self.set_content_visibility()

    def set_content_visibility(self):
        # TODO -- ask Sherry about mag vs. temp, etc...
        content_map = {
            'type': self.types,
            'brightness': self.brightness.contents,
            'redshift': self.redshift.contents,
            'width': self.width.contents,
            'temperature': self.temperature.contents,
            'index': self.index.contents
        }
        new_contents = [self.title.contents] + [value for key, value in content_map.items() if key in etc.source.active_parameters] + [self.upload]
        # In order to size properly, first set to []
        self.contents.children = []
        self.contents.children = new_contents
        js.page_loaded()


class atmosphere_panel:

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol'], sizing_mode='scale_width'), name='atmosphere_panel', sizing_mode='scale_width', css_classes=['input_section'])


    def reset(self):
        self.contents.children = [Div(css_classes=['loading-symbol'], sizing_mode='scale_width')]


    def load(self):
        self.title = section_title('Atmosphere')
        self.airmass_error_text = f'Airmass requires a value between {etc.atmosphere._airmass_index[0].value} and {etc.atmosphere._airmass_index[-1].value} {etc.atmosphere.airmass.unit}'
        self.water_vapor_error_text = f'Water vapor requires a value between {etc.atmosphere._water_vapor_index[0].value} and {etc.atmosphere._water_vapor_index[-1].value} {etc.atmosphere.water_vapor.unit}'

        self.seeing = quantity_input('atmosphere.seeing', 'Seeing:', etc.atmosphere.seeing.value, ['arcsec'], str(etc.atmosphere.seeing.unit), increment=0.1, low=0, css_classes=['seeing_input'])
        self.airmass = quantity_input('atmosphere.airmass', 'Airmass:', etc.atmosphere.airmass.value, error_text=self.airmass_error_text, increment=0.1, css_classes=['airmass_input'])
        self.water_vapor = quantity_input('atmosphere.water_vapor', 'Water Vapor:', etc.atmosphere.water_vapor.value, ['mm', 'cm'], str(etc.atmosphere.water_vapor.unit), error_text=self.water_vapor_error_text, increment=0.5, css_classes=['water_vapor'])

        self.contents.children = [self.title.contents, self.seeing.contents, self.airmass.contents, self.water_vapor.contents]


class instrument_panel:

    def binning_callback(self, attr, old, new):
        etc.set_parameter('instrument.binning', [int(new[0]), int(new[-1])])
        update_results()

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol'], sizing_mode='scale_width'), name='instrument_panel', sizing_mode='scale_width', css_classes=['input_section'])
        

    def reset(self):
        self.contents.children = [Div(css_classes=['loading-symbol'], sizing_mode='scale_width')]


    def load(self):
        self.title = section_title('Instrument')
        current_slit = f'{etc.instrument.slit_width.to(u.arcsec).value}" x {etc.instrument.slit_length.to(u.arcsec).value}"'
        slit_list = [f'{u.Quantity(x[0]).to(u.arcsec).value}" x {u.Quantity(x[1]).to(u.arcsec).value}"' for x in etc.instrument.config.slits]
        self.slit = Select(title='Slit:', value=current_slit, options=slit_list, width=300, sizing_mode='scale_width', css_classes=['help-icon'])
        # TODO -- add slit functionality, including "custom" option in dropdown (for appropriate instruments), which opens up a input row with "width" "length" and "unit"
        self.mode = dropdown_input('mode', 'Mode:', etc.instrument.mode, etc.instrument.config.modes)
        # TODO -- add grating, grism, and filter dependent on etc.instrument!
        self.binning = Select(title='CCD Binning:', value=f'{int(etc.instrument.binning[0].value)}x{int(etc.instrument.binning[1].value)}', options=[f'{int(b[0])}x{int(b[1])}' for b in etc.instrument.config.binning_options], width=300, sizing_mode='scale_width')
        self.binning.on_change('value', self.binning_callback)
        self.contents.children = [self.title.contents, self.mode.contents, self.slit, self.binning]

class section_title:

    def __init__(self, text):
        self.contents = column(Paragraph(text=text, margin=(5,5,0,5), sizing_mode='scale_width', css_classes=['section-title']), Div(css_classes=['hrule'], sizing_mode='scale_width'), sizing_mode='scale_width', margin=(0,0,-10,0), css_classes=['input_section'])


class big_number:

    def __init__(self, big, small):
        self.contents = column(Paragraph(text=big, css_classes=['sidebar-big', 'center']), Paragraph(text=small, css_classes=['sidebar-small', 'center']), Div(css_classes=['hrule', 'center'], sizing_mode='scale_width'), css_classes=['center'], sizing_mode='scale_width')


class instruction_text:

    def __init__(self):
        self.contents = column(name='instructions', sizing_mode='scale_width')
        with open('static/gui_instructions.txt') as file:
            for line in file:
                if len(line.strip()) > 0:
                    self.contents.children.append(Paragraph(text=line, sizing_mode='scale_width'))


class summary_panel:
    # TODO -- Add everything, make it look good, etc.

    

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol']), sizing_mode='scale_width', name='sidebar', css_classes=['input_section'])


    def reset(self):
        self.contents.children = [Div(css_classes=['loading-symbol'])]
        
    
    def load(self):

        # Define summary contents
        self.title = section_title('Results')  # Title
        # Empty text labels for each 
        self.flux_label = big_number('--- flam', 'source flux')
        self.wav_label = big_number('--- μm', 'wavelength')
        self.time_label = big_number('--- s', 'integration time')
        self.clk_label = big_number('--- s', 'clock time')
        self.exp_label = big_number('--- s', 'exposure')
        self.snr_label = big_number('---', 'S/N')

        # Download button, code from https://stackoverflow.com/questions/49388511/send-file-from-server-to-client-on-bokeh
        self.download_button = Button(label="Download Data", button_type="default", width=100, sizing_mode='scale_width', css_classes=['center', 'input_section'])
        download_js_code=Path('static/js/download_button.js').read_text()
        self.download_button.js_on_click(CustomJS(args=dict(source=results),code=download_js_code))

        # For sizing issues, add title first
        self.contents.children = [self.title.contents]
        
        # Next, add the rest of contents
        self.contents.children = [self.title.contents, 
            column(
                self.exp_label.contents,
                self.snr_label.contents,
                self.wav_label.contents,
                self.flux_label.contents,
                self.time_label.contents,
                self.clk_label.contents,
                self.download_button,
                css_classes=['sidebar-container']
            )
        ]
        
        # Define javascript to update this panel
        self.update_js = Path('static/js/update_summary.js').read_text()
        self.update = CustomJS(args={
            'time': self.time_label.contents.children[0],
            'exp': self.exp_label.contents.children[0],
            'snr': self.snr_label.contents.children[0],
            'flux': self.flux_label.contents.children[0],
            'wav': self.wav_label.contents.children[0],
            'source': results,
            'input': res.wavelength
        }, code=self.update_js)

        # Add callback to appropriate plots to trigger update
        res.snr_plot.js_on_event(MouseMove, self.update)
        res.exp_plot.js_on_event(MouseMove, self.update)
        res.counts_plot.js_on_event(MouseMove, self.update)
        results.js_on_change('data', self.update)
        
        # Replace data to manually trigger callback to finish loading
        results.data = dict(results.data)


class results_panel:
    # TODO -- Separate into individual graphs / sections!!


    # Highly experimental code for using a second source to display snr vs. exp --!
    def create_data(self, event):
            wavelengths = etc.wavelengths.copy()
            etc.set_parameter('wavelengths', [event.x * u.nm])
            if etc.target == 'signal_noise_ratio':
                 exposure = etc.exposure.copy()
                 etc.set_parameter('exposure', [str(item)+exp.units.value for item in self.new_source.data['x']])
                 y = etc.signal_noise_ratio.flatten().value
                 self.new_source.data['y'] = y
                 etc.exposure = exposure
            elif etc.target == 'exposure':
                 snr = etc.signal_noise_ratio.copy()
                 etc.set_parameter('signal_noise_ratio', self.new_source.data['x'])
                 y = etc.exposure.to(u.s).flatten().value
                 self.new_source.data['y'] = y
                 etc.signal_noise_ratio = snr
            etc.set_parameter('wavelengths', wavelengths)

    def __init__(self):
        self.contents = column(Div(css_classes=['loading-symbol']), name='results', sizing_mode='scale_both', css_classes=['input_section'])


    def reset(self):
        self.contents.children = [Div(css_classes=['loading-symbol'])]


    def load(self):

        # Vertical line to indicate & select wavelength
        self.wavelength = Span(location=etc.wavelengths[0].to(u.nm).value, dimension='height', line_color='black', line_dash='dashed')
        self.wavelength_js = CustomJS(args={'vline':self.wavelength}, code='vline.location=cb_obj.x;')
        self.vs_wavelength = Span(location=self.wavelength.location, dimension='height', line_color='#333', line_dash='solid')

        # Define tools to use in plots -- TODO pick better order
        plot_tools = 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, hover, help'
        
        # Define vs. plot
        self.vs_plot = figure(
            title=f'Wavelength: {int(self.vs_wavelength.location)} nm', 
            active_inspect='hover', 
            tools=plot_tools, 
            toolbar_location=None,
            width=500, 
            height=100, 
            tooltips=[('S/N', '$y{0.00}'), ('exp (s)', '$x{0}')], 
            sizing_mode='scale_width',
            name='vs_plot'
        )
        

        self.vs_wavelength_js = CustomJS(args={'vline':self.vs_wavelength, 'plot':self.vs_plot}, 
            code='plot.select_one("text").visible=false;plot.select_one("box").visible=false;vline.location=cb_obj.x;plot.title.text="Wavelength: "+Math.round(cb_obj.x)+"nm";')

        

        # Plot snr vs. wavelength
        self.snr_plot = figure(
            title='Signal to Noise Ratio',
            toolbar_location='above', 
            toolbar_sticky=False, 
            width=450, 
            height=100,
            tooltips=[('S/N', '$y{0.0}'), ('λ (nm)', '$x{0}')], 
            sizing_mode='scale_both'
        )
        self.snr_plot.toolbar = self.vs_plot.toolbar  # TESTING!
        self.snr_plot.sizing_mode = 'scale_both'
        self.snr_plot.xaxis.axis_label = 'wavelengths (nm)'
        self.snr_plot.yaxis.axis_label = 'signal to noise ratio'
        scatter = self.snr_plot.scatter(x='wavelengths', y='snr', source=results, alpha=0.5, size=6, legend_label='\u00A0')
        scatter.visible = False  # Initially start hidden
        self.snr_plot.line(x='wavelengths', y='snr', source=results, legend_label='')
        self.snr_plot.add_layout(self.vs_wavelength)
        self.snr_plot.add_layout(self.wavelength)
        self.snr_plot.output_backend = 'svg'
        self.snr_plot.legend.label_height=10
        self.snr_plot.legend.label_width=10
        self.snr_plot.legend.label_text_font_size = '10px'
        self.snr_plot.legend.spacing = 5
        self.snr_plot.legend.click_policy = 'hide'
        self.snr_plot.js_on_event(MouseMove, self.wavelength_js)
        self.snr_plot.js_on_event('tap', self.vs_wavelength_js)
        self.snr_plot.on_event('tap', self.create_data)
        

        # Plot exp vs. wavelength
        self.exp_plot = figure(
            title='Exposure Time',
            toolbar_location='above', 
            toolbar_sticky=False,
            sizing_mode='scale_width', 
            width=450, 
            height=100, 
            name='exp_plot',
            tooltips=[('exp (s)', '$y{0}'), ('λ (nm)', '$x{0}')], 
            y_range=(min(results.data['exposure'])*.8, 
            nanpercentile(results.data['exposure'], 50))
        )
        self.exp_plot.toolbar = self.vs_plot.toolbar  # TESTING!
        self.exp_plot.xaxis.axis_label = 'wavelengths (nm)'
        self.exp_plot.yaxis.axis_label = 'exposure time (s)'
        self.exp_plot.scatter(x='wavelengths', y='exposure', source=results, alpha=0.5, size=6, legend_label='\u00A0')
        line = self.exp_plot.line(x='wavelengths', y='exposure', source=results, legend_label='')
        line.visible = False  # Initially start hidden
        self.exp_plot.add_layout(self.vs_wavelength)
        self.exp_plot.add_layout(self.wavelength)
        self.exp_plot.output_backend = 'svg'
        self.exp_plot.legend.label_height=10
        self.exp_plot.legend.label_width=10
        self.exp_plot.legend.label_text_font_size = '10px'
        self.exp_plot.legend.click_policy = 'hide'
        self.exp_plot.js_on_event(MouseMove, self.wavelength_js)
        self.exp_plot.js_on_event('tap', self.vs_wavelength_js)
        self.exp_plot.on_event('tap', self.create_data)
        # Custom JS callback for the plot reset button to ensure proper y_range handling
        js_reset_callback = '''
        const exp = src.data['exposure'].filter( value => !Number.isNaN(value) );
        if (exp.length > 0){
            ax.start = Math.min(...exp) * 0.8;
            ax.end = exp.sort((a, b) => a - b)[Math.floor(exp.length / 2)];
        }
        '''
        self.exp_plot.js_on_event(Reset, CustomJS(args={'src':results, 'ax':self.exp_plot.y_range}, code=js_reset_callback))


        # Plot 2
        self.counts_plot = figure(
            title='Counts',
            toolbar_location=None,
            width=500, 
            height=100, 
            tooltips=[('count (ADU/px)', '$y{0}'), ('λ (nm)', '$x{0}')], 
            y_axis_type='log', 
            sizing_mode='scale_width'
        )
        self.counts_plot.toolbar = self.vs_plot.toolbar  # TESTING!
        self.counts_plot.xaxis.axis_label = 'wavelengths (nm)'
        self.counts_plot.yaxis.axis_label = 'Counts (ADU/px)'

        self.counts_plot.line(x='wavelengths', y='source', source=results, legend_label='Source', line_color='#009E73')
        self.counts_plot.line(x='wavelengths', y='background', source=results, legend_label='Background', line_color='#0072B2')
        self.counts_plot.line(x='wavelengths', y='read_noise', source=results, legend_label='Read Noise', line_color='#CC79A7')
        self.counts_plot.line(x='wavelengths', y='dark_current', source=results, legend_label='Dark Current', line_color='#000000')
        self.counts_plot.line(x='wavelengths', y='nonlinear', source=results, legend_label='Non-linearity', line_color='#D55E00', line_dash='dashed')
        #self.counts_plot.add_layout(self.counts_plot.legend[0], 'right')  # For moving legend outside plot
        self.counts_plot.add_layout(self.vs_wavelength)
        self.counts_plot.add_layout(self.wavelength)
        self.counts_plot.legend.label_height=10
        self.counts_plot.legend.label_width=10
        self.counts_plot.legend.label_text_font_size = '10px'
        self.counts_plot.legend.click_policy = 'hide'
        self.counts_plot.legend.spacing = 0  # Figure out whether or not this line helps!
        self.counts_plot.output_backend = 'svg'
        self.counts_plot.js_on_event(MouseMove, self.wavelength_js)
        self.counts_plot.js_on_event('tap', self.vs_wavelength_js)
        self.counts_plot.on_event('tap', self.create_data)
        # Share toolbar test -- !
        self.counts_plot.js_link('toolbar', self.snr_plot, 'toolbar')
        self.snr_plot.js_link('toolbar', self.counts_plot, 'toolbar')


        # EXPERIMENTAL CODE !!! --- creating second data source with snr vs. exp
        self.new_source = ColumnDataSource({'x':linspace(0, 7200, 25), 'y':[0]*25})
        self.create_data(Tap(model=None, x=self.vs_wavelength.location))
        self.vs_box = BoxAnnotation(left_units='screen', bottom_units='screen', bottom=0, left=0, fill_color="#FFF", fill_alpha=0.6, name='box')
        self.vs_text = Label(x=0, y=0, x_units='screen', y_units='screen', text='Click on the plots above to set wavelength', text_align='center', 
            text_baseline='middle', text_font_size='2.5em', text_alpha=0.7, name='text')
        self.vs_plot.xaxis.axis_label = 'exposure (s)'
        self.vs_plot.yaxis.axis_label = 'Signal to Noise Ratio'
        self.vs_plot.line(x='x', y='y', source=self.new_source)
        self.vs_plot.output_backend = 'svg'
        #self.vs_text.x = (self.new_source.data['x'][0]+self.new_source.data['x'][-1])/2
        #self.vs_text.y = (self.new_source.data['y'][0]+self.new_source.data['y'][-1])/2
        self.vs_plot.add_layout(self.vs_box)
        self.vs_plot.add_layout(self.vs_text)
        

        self.contents.children = [self.exp_plot, self.snr_plot, self.counts_plot, self.vs_plot]
        if etc.target == 'exposure':
            self.snr_plot.visible = False
        elif etc.target == 'signal_noise_ratio':
            self.exp_plot.visible = False

        # CURRENTLY BROKEN (x doesn't update) -- FIX!!
        #res.create_data(Tap(model=None, x=res.wavelength.location))
        results.on_change('data', lambda attr, old, new: self.create_data(Tap(model=None, x=self.vs_wavelength.location)))


    def reload(self):
        if exp.target.value == 'signal to noise ratio':
            self.new_source.data = {'x': linspace(exp.exposure_min.value, exp.exposure_max.value, 100) if exp.exposure_max.value > exp.exposure_min.value else linspace(0, 7200, 100), 'y':[0]*100}
            self.create_data(Tap(model=None, x=self.vs_wavelength.location))
            self.vs_plot.xaxis.axis_label = 'exposure (s)'
            self.vs_plot.yaxis.axis_label = 'Signal to Noise Ratio'
            self.vs_plot.tools[-2].tooltips=[('S/N', '$y{0.00}'), ('exp (s)', '$x{0}')]  # Second to last tool = HoverTool
            self.exp_plot.visible = False
            self.snr_plot.visible = True
            #page_loaded()
        elif exp.target.value == 'exposure':
            self.new_source.data = {'x': linspace(exp.snr_min.value, exp.snr_max.value, 25) if exp.snr_max.value > exp.snr_min.value else linspace(0, 20, 25), 'y': [0]*25}
            self.create_data(Tap(model=None, x=self.vs_wavelength.location))
            self.vs_plot.xaxis.axis_label = 'Signal to Noise Ratio'
            self.vs_plot.yaxis.axis_label = 'exposure (s)'
            self.vs_plot.tools[-2].tooltips=[('exp (s)', '$y{0}'), ('S/N', '$x{0.00}')]
            if self.exp_plot.visible and not isnan(etc.exposure[0].value).all():
                self.exp_plot.y_range.start = min(etc.exposure[0].value)*.8
                self.exp_plot.y_range.end = nanpercentile(etc.exposure[0].value, 50)
            self.snr_plot.visible = False
            self.exp_plot.visible = True
            #page_loaded()
    

class instrument_menu:

    def callback(self, attr, old, new):
        try:
            etc.set_parameter('instrument.name', etc.config.instruments[new])
            update_results()
        except Exception as e:
            js.show_alert('This instrument has not yet been added, and is only here because it looks good :)')
            self.contents.active = old

    def __init__(self):
        # Initialize a bunch of empty tabs to avoid js error msg when setting tabs.active to a tab that doesn't exist
        self.contents = Tabs(tabs=[Panel(child=Div(text='<div style="width: 90vw;"></div>'), title='\u00A0'*10) for i in range(10)], name='instruments', sizing_mode='scale_width')

    def load(self):
        # Set correct tab active before defining tabs because it looks better as it loads
        self.contents.active = [i for i, x in enumerate(etc.config.instruments) if x.lower() == etc.instrument.name.lower()][0]
        self.contents.tabs = [ Panel(child=Div(sizing_mode='scale_width'), title=instrument.upper()) for instrument in etc.config.instruments ]
        self.contents.on_change('active', self.callback)


class py2js:
    
    def show_alert(self, msg):
        self.alert_container.tags = [msg]

    def set_cookies(self, obj):
        self.cookie_container.tags = [obj]

    def page_loaded(self):
        self.page_loaded_container.tags = [True] if self.page_loaded_container.tags != [True] else [False]

    def reset_contents_callback(self, attr, old, new):
        if attr == 'tags' and old == [False] and new == [True]:
            exp.reset()
            res.reset()
            src.reset()
            atm.reset()
            instr.reset()
            summary.reset()
            menu.load()
            exp.load()
            res.load()
            src.load()
            atm.load()
            instr.load()
            summary.load()
            self.page_loaded()
            self.reset_contents_container.tags = [False]


    def __init__(self):
        # Load javascript and define CustomJS callback
        js_code = Path('static/js/python_js_communication.js').read_text()
        titles = yaml.safe_load(open('static/mouseover_text.yaml'))
        js_callback = CustomJS(args={'titles':titles}, code=js_code)


        # Define DOM objects
        self.alert_container = Div(name='alert_container', visible=False)
        self.cookie_container = Div(name='cookie_container', visible=False)
        self.page_loaded_container = Div(name='page_loaded_container', visible=False)
        self.reset_contents_container = Div(name='reset_contents_container', tags=[False], visible=False)

        # Assingn js callbacks
        self.alert_container.js_on_change('tags', js_callback)
        self.cookie_container.js_on_change('tags', js_callback)
        self.page_loaded_container.js_on_change('tags', js_callback)
        self.reset_contents_container.on_change('tags', self.reset_contents_callback)


class reset_button():

    def __init__(self):

        self.reset_js = CustomJS(code=Path('static/js/reset_button.js').read_text())
        self.contents = Button(label='Reset Calculator', button_type='default', name='reset_button', width_policy='min')
        self.contents.js_on_click(self.reset_js)
        

# FUNCTION DEFINITIONS

def load_query(etc):
    try:
        query = urlparse(curdoc().session_context.request.uri).query
        whitelist_regex = r'[^a-zA-Z0-9\.\=\[\]\-()&+_,]'  # Allowed characters are alphanumerics and . = [ ] - ( ) & + _ ,
        query = sub(whitelist_regex,'', query)  # Remove all non-allowed characters from query string
        if len(query) > 0:
            query = dict(qc.split("=") for qc in query.split("&"))
            # Convert any lists from string
            for key, val in query.items():
                if val.startswith('[') and val.endswith(']'):
                    query[key] = [x.strip() for x in val[1:-1].split(',')]
        # Set parameters from query
        if len(query) > 0:
            etc.set_parameters(query)
            return True
    except Exception as e:
        js.show_alert(f'Error processing url query:\n{e}')
        
    return False


def load_cookie(etc):
    if 'Cookie' in curdoc().session_context.request.headers.keys():
        cookies = curdoc().session_context.request.headers['Cookie'].split(';')
        settings = [cookie for cookie in cookies if cookie.strip().startswith('etcsettings=')]
        if settings:
            try:
                etc.set_parameters(settings[0].replace('etcsettings=',''))
            except Exception as e:
                print(f"Invalid cookie value -- {e}")


def load_contents(event):
    # Initialize ETC
    global etc
    etc = exposure_time_calculator()
    # Set ETC parameters based on url query, if present
    query = load_query(etc)
    # Otherwise, set ETC parameters based on stored cookies
    if not query:
        load_cookie(etc)
    
    # Load app contents
    update_results()
    menu.load()
    exp.load()
    res.load()
    src.load()
    atm.load()
    instr.load()
    summary.load()
    js.page_loaded()




# Initialize objects
global etc
etc = None
results = ColumnDataSource()
menu = instrument_menu()
exp = exposure_panel()
atm = atmosphere_panel()
src = source_panel()
res = results_panel()
summary = summary_panel()
instr = instrument_panel()
help = instruction_text()
reset = reset_button()
js = py2js()
curdoc().add_root(res.contents)
curdoc().add_root(menu.contents)
curdoc().add_root(exp.contents)
curdoc().add_root(atm.contents)
curdoc().add_root(src.contents)
curdoc().add_root(summary.contents)
curdoc().add_root(instr.contents)
curdoc().add_root(help.contents)
curdoc().add_root(reset.contents)
curdoc().add_root(js.alert_container)
curdoc().add_root(js.cookie_container)
curdoc().add_root(js.page_loaded_container)
curdoc().add_root(js.reset_contents_container)
curdoc().title = 'WMKO ETC'

# Once initial loading screen is present, load app
curdoc().on_event(DocumentReady, load_contents)

if __name__ == '__main__':
    print('hi')