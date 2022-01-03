
// Method to convert between units
const convertUnits = (value, unitFrom, unitTo, requiredInfo) => {
    // Available units, divided into types
    const units = {
        length: {
            'angstrom': 10**-10,
            'nm': 10**-9,
            'um': 10**-6,
            'mm': 10**-3,
            'cm': 10**-2,
            'm': 1,
            'km': 10**3
        },
        angle: {
            'marcsec': 10**-3,
            'milliarcsec': 10**-3,
            'arcsec': 1,
            '"': 1,
            '\'': 60,
            'arcmin': 60,
            'degree': 3600,
            'radian': 206265,
        },
        time: {
            'ns': 10**-9,
            'us': 10**-6,
            'ms': 10**-3,
            's': 1,
            'min': 60,
            'minute': 60,
            'hr': 3600,
            'hour': 3600,
            'day': 86400
        },
        temperature: {
            'k': [1, 0],
            'kelvin': [1, 0],
            'c': [1, 273.15],
            'celsius': [1, 273.15],
            'f': [1.8, 459.67],
            'fahrenheit': [1.8, 459.67],
            'r': [1.8, 0],
            'rankine': [1.8, 0]
        },
        flux: {
            'mag(ab)': [],
            'abmag': [],
            'mag(vega)': [],
            'vegamag': [],
            'mag(st)': [],
            'stmag': [],
            'jy': [],
            'janksy': [],
            'flam': [],
            'photlam': []
        }
    }

    // Get type of both units
    const type = Object.keys(units).filter( type => 
        unitFrom.toLowerCase() in units[type] && unitTo.toLowerCase() in units[type]
    );

    // If units didn't have the same type, throw error
    if (type.length === 0) {
        throw 'Cannot convert from '+unitFrom+' to '+unitTo;
    }

    // Otherwise, convert based on type of unit
    if (['length', 'angle', 'time'].includes(type[0])) {
        return value * units[type[0]][unitFrom.toLowerCase()] / units[type[0]][unitTo.toLowerCase()];
    }

    if (type[0] === 'temperature') {
        if (['k','kelvin'].includes(unitTo.toLowerCase()) ||
            ['k','kelvin'].includes(unitFrom.toLowerCase()))
        {   // If one of the units is kelvin, translate, scale, and translate to convert
            const from = units.temperature[unitFrom.toLowerCase()];
            const to = units.temperature[unitTo.toLowerCase()];
            return (value + from[1]) * to[0] / from[0] - to[1];
        } else {
            // Otherwise, convert to Kelvin and back
            return convertUnits( convertUnits(value, unitFrom, 'K'), 'K', unitTo );
        }
    }

    if (type[0] === 'flux') {
        // TODO
        return value;
    }

}


// Define Bokeh source and plots
const createPlots = (source, vsSource) => {
    
    // Create vertical lines for marking wavelengths
    const resPanelWavelength = new Bokeh.Span({
        location: 0,
        dimension: 'height',
        line_color: 'black',
        line_dash: 'dashed'
    });
    const vsPlotWavelength = new Bokeh.Span({
        location: 0,
        dimension: 'height',
        line_color: '#333',
        line_dash: 'solid'
    });
    const callbacks = { 
        mousemove: [new Bokeh.CustomJS({ args: {w: resPanelWavelength}, code: 'w.location=cb_obj.x; updateResults()' })],
        tap: [new Bokeh.CustomJS({ args: {w: vsPlotWavelength}, code: 'w.location=cb_obj.x; updateVSPlot()' })]
    };



    // Define first plot, snr/exp vs. wavelength
    const wavelengthPlot = new Bokeh.Plotting.figure({
        name: 'plot',
        title: 'Signal to Noise Ratio',
        plot_width: 450,
        plot_height: 100,
        min_width: 250,
        sizing_mode: 'scale_width',
        tools: 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, help, hover'
    });
    const scatter = wavelengthPlot.scatter({field: 'wavelengths'}, {field: 'signal_noise_ratio'}, {
        source: source, 
        alpha: 0.5, 
        size: 6, 
        legend_label: '\u00A0'
    });
    const line = wavelengthPlot.line({field: 'wavelengths'}, {field: 'signal_noise_ratio'}, {
        source: source, 
        legend_label: ''
    });
    wavelengthPlot.toolbar.tools.at(-1).tooltips = [['S/N', '$y{0.0}'], ['λ (nm)', '$x{0}']];
    wavelengthPlot.xaxis[0].axis_label = 'Wavelength (nm)';
    wavelengthPlot.yaxis[0].axis_label = 'Signal to Noise Ratio';
    scatter.visible = false;  // Initially start hidden
    wavelengthPlot.output_backend = 'svg';
    wavelengthPlot.legend.label_height=10;
    wavelengthPlot.legend.label_width=10;
    wavelengthPlot.legend.label_text_font_size = '10px';
    wavelengthPlot.legend.click_policy = 'hide';
    wavelengthPlot.add_layout(resPanelWavelength);
    wavelengthPlot.add_layout(vsPlotWavelength);
    // Add event listener for mousemove on plot
    wavelengthPlot.js_event_callbacks = callbacks;

    // Define second plot, counts vs. wavelength
    const countsPlot = new Bokeh.Plotting.figure({
        title: 'Counts',
        y_axis_type: 'log',
        plot_width: 450,
        plot_height: 100,
        min_width: 250,
        sizing_mode: 'scale_width',
        tools: 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, help, hover'
    });
    countsPlot.line({field: 'wavelengths'}, {field: 'source_count_adu'}, { source: source, legend_label: 'Source', line_color: '#009E73' });
    countsPlot.line({field: 'wavelengths'}, {field: 'background_count_adu'}, { source: source, legend_label: 'Background', line_color: '#0072B2' });
    countsPlot.line({field: 'wavelengths'}, {field: 'read_noise_count_adu'}, { source: source, legend_label: 'Read Noise', line_color: '#CC79A7' });
    countsPlot.line({field: 'wavelengths'}, {field: 'dark_current_count_adu'}, { source: source, legend_label: 'Dark Current', line_color: '#000000' });
    countsPlot.line({field: 'wavelengths'}, {field: 'nonlinear_depth_adu'}, { source: source, legend_label: 'Non-linearity', line_color: '#D55E00', line_dash: 'dashed' });
    countsPlot.toolbar.tools.at(-1).tooltips = [['Count (ADU/px)', '$y{0}'], ['λ (nm)', '$x{0}']];
    countsPlot.xaxis[0].axis_label = 'wavelengths (nm)'
    countsPlot.yaxis[0].axis_label = 'Counts (ADU/px)'
    countsPlot.legend.label_height = 10;
    countsPlot.legend.label_width = 10;
    countsPlot.legend.label_text_font_size = '10px';
    countsPlot.legend.click_policy = 'hide';
    countsPlot.legend.spacing = 0;
    countsPlot.output_backend = 'svg';
    countsPlot.add_layout(resPanelWavelength);
    countsPlot.add_layout(vsPlotWavelength);
    // Add event listener for mousemove on plot
    countsPlot.js_event_callbacks = callbacks;


    // Define third plot, exp vs. snr
    const vsPlot = new Bokeh.Plotting.figure({
        title: 'Wavelength: ',
        plot_width: 450,
        plot_height: 100,
        min_width: 250,
        sizing_mode: 'scale_width',
        tools: 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, help, hover'
    });
    vsPlot.line({field: 'exposure'}, {field: 'signal_noise_ratio'}, { source: vsSource });
    vsPlot.toolbar.tools.at(-1).tooltips = [['S/N', '$y{0.0}'], ['exp (s)', '$x{0}']];
    vsPlot.output_backend = 'svg';


    // Define grid of plots
    const grid = new Bokeh.Plotting.gridplot(
        [[wavelengthPlot], [countsPlot], [vsPlot]], {
        merge_tools: true,
        width: 450,
        height: 100,
        sizing_mode: 'scale_width'
    });

    Bokeh.Plotting.show(grid, '#output-plots');

    return {resPanelWavelength: resPanelWavelength, vsPlotWavelength: vsPlotWavelength, wavelengthPlot: wavelengthPlot, vsPlot: vsPlot};

}


// Make API request to get info
const apiRequest = async (query, parameters) => {

    // Add parameters to query
    for (const [key, value] of Object.entries(parameters)){
        if (value instanceof Array){
            query += '&' + key + '=[' + value + ']';
        } else {
            query += '&' + key + '=' + value;
        }
    }

    // Send fetch request and return data
    const request = await fetch('http://vm-internship:8080'+query);
    const data = request.status === 200 ? request.json() : {};
    return data;
}


const createDataSources = () => {
    // Create sources, define with placeholder arrays
    const source = new Bokeh.ColumnDataSource({ data: { 
        'wavelengths': [],
        'exposure': [],
        'source_count_adu': [],
        'background_count_adu': [],
        'read_noise_count_adu': [],
        'dark_current_count_adu': [],
        'signal_noise_ratio': [],
        'nonlinear_depth_adu': [],
        'clock_time': [],
        'efficiency': [],
        'source_flux': []
    }});

    const vsSource = new Bokeh.ColumnDataSource({ data: {
        'exposure': [],
        'signal_noise_ratio': []
    }});

    return {source: source, vsSource: vsSource};
}

const updateDataSource = (source, data) => {
    // Format data so that every column is the same length
    for (const [key, value] of Object.entries(data)) {
        if (typeof value === 'number') {
            data[key] = new Array(data.wavelengths.length).fill(value);
        } else if (value.length === 1 && typeof value[0] === 'object') {
            data[key] = value[0];
        } else if (value.length === 1) {
            data[key] = new Array(data.wavelengths.length).fill(value[0]);
        } else if (typeof value[0] === 'object') {
            data[key] = value.map(x => x[0]);
        }
    }

    // Convert angstrom to nm
    if (data.wavelengths) {
        data.wavelengths = data.wavelengths.map( x => x/10 );
    }

    // Update ColumnDataSource
    source.data = data;
    source.change.emit();
}

const updateResults = () => {
    // Get wavelength to use
    const wavelength = resPanelWavelength.location;
    // Set up interpolation
    const idx = source.data['wavelengths'].indexOf( source.data['wavelengths'].filter( x => x <= wavelength ).at(-1) );
    const ratio = (wavelength - source.data['wavelengths'][idx]) / (source.data['wavelengths'][idx+1] - source.data['wavelengths'][idx]);
    // Loop through results and update
    for (const id of ['exposure', 'signal-noise-ratio','source-flux','wavelengths','clock-time','efficiency']) {
        const upper = source.data[id.replaceAll('-','_')][idx+1];
        const lower = source.data[id.replaceAll('-','_')][idx];
        document.querySelector('#output-'+id).value = lower + (upper - lower) * ratio;
    }
    // Convert units
    if (document.querySelector('#output-wavelengths').unit === '\u00b5m') {
        document.querySelector('#output-wavelengths').value /= 1000;
    }

}

const updateVSPlot = () => {
    // Get wavelength and set corresponding title
    const wavelength = vsPlotWavelength.location;
    vsPlot.title.text = 'Wavelength: ' + wavelength.toFixed(0) + 'nm';
    // Update data for vs. plot
    apiRequest(getQuery(true), getParameters(true)).then( data => updateDataSource(vsSource, data) );
    // TODO -- change axes, tooltips, etc...
}

const updateUI = (parameters) => {
    // Loop through all inputs in app
    document.querySelectorAll('input-select, input-spin, input-slider').forEach( input => {
        const name = input.id.replaceAll('-','_');
        // If id is not parameter, parameter-unit, parameter-min, or parameter-max, then hide inactive element 
        if (!(name in parameters || name.replace('_unit','') in parameters || 
            name.replace('_min','') in parameters || name.replace('_max','') in parameters))
        {
            input.parentElement.classList.add('hidden');
        } else if (!name.endsWith('unit') && !name.endsWith('min') && !name.endsWith('max')) {
            // Otherwise, get value from parameters
            let value = parameters[name].value;
            // If needed, convert value to appropriate unit
            if (document.querySelector('#'+input.id+'-unit')) {
                value = convertUnits(value, parameters[name].unit, document.querySelector('#'+input.id+'-unit').value);
                input.unit = parameters[name].unit;
            }
            // If min and max exist, set to defaults of 0 and 2 * value
            if (document.querySelector('#'+input.id+'-min')) {
                document.querySelector('#'+input.id+'-min').value = 0;
            }
            if (document.querySelector('#'+input.id+'-max')) {
                document.querySelector('#'+input.id+'-max').value = 2 * value;
            }
            // If available, set options for select
            if (parameters[name].options) {
                input.options = parameters[name].options;
            }
            // Set value
            guiInactive = true;
            input.value = value;
            guiInactive = false;

            input.parentElement.classList.remove('hidden');
        } else {
            input.parentElement.classList.remove('hidden');
        }
    });

}

const update = () => {
    // Display loading symbols on output
    document.querySelectorAll('.panel.output').forEach(el => el.classList.add('loading'));
    // Get results from ETC, update ui and data
    apiRequest(getQuery(false), getParameters(false)).then( data => {
        updateUI(data.parameters);
        updateDataSource(source, data);
        // Change results to reflect new data
        updateResults();
        // Get vs. data and update plot
        updateVSPlot();
        // Done updating document, remove loading symbols
        document.querySelectorAll('.panel.output.loading').forEach(el => el.classList.remove('loading'));
    // On error, display to user
    }).catch( error => {
        alert('Error:\n'+error);
    });
    
}

const getQuery = (isForVSPlot) => {
    let query = '?return=[exposure,signal_noise_ratio'
    if (!isForVSPlot) {
        query += ',source_count_adu,read_noise_count_adu,clock_time,' +
                'wavelengths,background_count_adu,dark_current_count_adu,' +
                'efficiency,source_flux,nonlinear_depth_adu,parameters';
    }
    query += ']';
    return query;
}

const getParameters = (isForVSPlot) => {
    const options = [
        'exposure', 'signal_noise_ratio', 'dithers', 'repeats', 'coadds', 'reads',
        'type', 'flux', 'wavelength_band', 'redshift', 'index', 'temperature', 'width',
        'mode', 'slit', 'binning', 'grating', 'grism',
        'seeing', 'airmass', 'water_vapor', 'target' // Target is last because it must be set after exp. or snr
    ];
    const parameters = isForVSPlot ? {wavelengths: [vsPlotWavelength.location+'nm']} : {};

    for (parameter of options) {
        const id = '#'+parameter.replaceAll('_','-');
        const element = document.querySelector(id);
        if (!!element && !element.parentElement.classList.contains('hidden') && element.value){
            const unit = !!document.querySelector(id+'-unit') ? document.querySelector(id+'-unit').value : '';
            if (isForVSPlot && (id==='#exposure' || id==='#signal-noise-ratio')){
                // For vs. plot, get range of exp/snr from min and max elements
                const start = parseFloat(document.querySelector(id+'-min').value);
                const stop = parseFloat(document.querySelector(id+'-max').value);
                const step = (stop - start) / (25-1); // Hard-coded value of 25 points
                const list = Array(25).fill(start).map((x, i) => x + i * step);
                parameters[parameter] = list.map(x => x+unit);
            } else {
                parameters[parameter] = element.value + unit;
            }
        }
    }
    return parameters;
}

const calculatorCallback = () => {
    const parameters = getParameters();

}

// Called when page loads
setup = () => {

    // Define instrument-menu click behavior
    document.querySelectorAll('.instrument-menu .instrument').forEach( 
        element => element.addEventListener('click', event => {
            document.querySelectorAll('.instrument').forEach( (el) => el.classList.remove('selected'));
            element.classList.add('selected');
            apiRequest({'instrument.name': element.textContent});
        })
    );

    // Define reset button click handling
    document.querySelector('button#reset').addEventListener('click', event => {
        //apiRequest({});
    });

    // Define mobile collapse / expand behavior
    document.querySelectorAll('div.section-title, div.loading-overlay').forEach( (el) => {
        el.addEventListener('click', (event) => {
            // Get anscestor panel
            const toggle = el.closest('div.panel');

            // On click, toggle css .open class
            if (toggle.classList.contains('open')) {
                toggle.classList.remove('open');
            } else {
                toggle.classList.add('open');
            }
        });
    });

    // Read in mouseover text file
    fetch('static/mouseover_text.json').then(response => 
        response.json() ).then( data => { 
            // Add tooltips to appropriate elements based on file
            for (const [name, text] of Object.entries(data)) {
                const el = document.getElementById(name);
                if (el) {
                    el.info = text.trim();
                    // Set tooltip according to screen position
                    // const tooltip = el.querySelector('label.info');
                    // if (tooltip.getBoundingClientRect().x > window.innerWidth/2) {
                    //     tooltip.classList.add('right');
                    // }
                }
            };
        }).catch(error => console.log(error));

    // Read in instructions text file
    fetch('static/gui_instructions.txt').then(response =>
        response.text() ).then( text => {
            // Add paragraph element to instructions for line of text
            const instructions = document.getElementById('instructions');
            for (line of text.split('\n')) {
                const paragraph = document.createElement('p');
                paragraph.textContent = line.trim();
                instructions.appendChild(paragraph);
            }
        }).catch(error => console.log(error));


    // Flag to avoid triggering callbacks from within callback
    guiInactive = false;
    // Define ColumnDataSource
    ({source, vsSource} = createDataSources());
    // Define output plots
    ({resPanelWavelength, vsPlotWavelength, wavelengthPlot, vsPlot} = createPlots(source, vsSource));
    // Update inputs and outputs with values from API
    update();

    // Define callbacks on value changes for inputs
    document.querySelectorAll('input-select, input-spin, input-slider').forEach( input => {
        // If unit, convert values for corresponding elements
        if (input.id.endsWith('unit')) {
            const number = document.querySelector('#'+input.id.replace('-unit',''));
            const min = document.querySelector('#'+input.id.replace('-unit','-min'));
            const max = document.querySelector('#'+input.id.replace('-unit','-max'));
            input.addEventListener('change', event => {
                const oldNumberValue = number.value;
                guiInactive = true;
                if (min && max) {
                    min.value = convertUnits(min.value, event.oldValue, event.newValue);
                    max.value = convertUnits(max.value, event.oldValue, event.newValue);
                } else {
                    const oldMaxValue = number.max;
                    number.min = convertUnits(number.min, event.oldValue, event.newValue);
                    number.max = convertUnits(oldMaxValue, event.oldValue, event.newValue);
                }
                number.value = convertUnits(oldNumberValue, event.oldValue, event.newValue);
                number.unit = event.newValue;
                guiInactive = false;
            });
        // If minimum, set value for corresponding element
        } else if (input.id.endsWith('min')) {
            const number = document.querySelector('#'+input.id.replace('-min',''));
            input.addEventListener('change', () => {
                guiInactive = true;
                number.min = input.value;
                guiInactive = false;
            });
        // If maximum, set value for corresponding element
        } else if (input.id.endsWith('max')) {
            const number = document.querySelector('#'+input.id.replace('-max',''));
            input.addEventListener('change', () => {
                guiInactive = true;
                number.max = input.value;
                guiInactive = false;
            });
        // Otherwise, call update() to make API call w/ changed value and display results
        } else if (!input.id.endsWith('min') && !input.id.endsWith('max')) {
            input.addEventListener('change', () => {if (!guiInactive) { update() } });
        }
    });

};


Bokeh.set_log_level('error');
window.addEventListener('DOMContentLoaded', setup);

// TODO -- Handle GUI changes in JS, only call updateUI on load!
// TODO -- Store values in cookies
// TODO -- Change plots on target callback