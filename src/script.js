// Copyright (c) 2022, W. M. Keck Observatory
// All rights reserved.

// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.


// load JSON file to get vega flux
let vegaFlux = fetch('src/static/vega_flux.json').then( res => res.json() ).catch(error => console.log(error));
// Method to convert between units, wavelength in Angstrom required for flux density conversions
const convertUnits = (value, unitFrom, unitTo, wavelength) => {
    // Available units, divided into types
    const units = {
        length: {
            'angstrom': 10**-10,
            'nm': 10**-9,
            'nanometer': 10**-9,
            'um': 10**-6,
            'micrometer': 10**-6,
            'micron': 10**-6,
            'mm': 10**-3,
            'millimeter': 10**-3,
            'cm': 10**-2,
            'centimeter': 10**-2,
            'm': 1,
            'meter': 1,
            'km': 10**3,
            'kilometer': 10**3
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
            // unit: [ convert from photlam, convert to photlam ]
            // From https://pysynphot.readthedocs.io/en/latest/units.html and https://hea-www.harvard.edu/~pgreen/figs/Conversions.pdf
            'mag(ab)': [ x => -2.5 * Math.log10(5.1*10**12 * x * wavelength) + 48.6,
                        x => 10**(-(x - 48.6)/2.5) / (wavelength * 5.1*10**12) ],
            'abmag': [ x => -2.5 * Math.log10(5.1*10**12 * x * wavelength) + 48.6,
                        x => 10**(-(x - 48.6)/2.5) / (wavelength * 5.1*10**12) ],
                // TODO -- need more precision on 5.1*10**12 from ABmag
            'mag(vega)': [ x => -2.5 * Math.log10(x/vega(wavelength)),
                            x => vega(wavelength) * 10**( -0.4 * x )],
            'vegamag': [ x => -2.5 * Math.log10(x/vega(wavelength)),
                            x => vega(wavelength) * 10**( -0.4 * x )],
            'mag(st)': [ x => -2.5 * Math.log10(1.99*10**-8 * x / wavelength) - 21.1,
                            x => 10**(-(x + 21.1)/2.5) * wavelength * 5.03*10**7 ],
            'stmag': [ x => -2.5 * Math.log10(1.99*10**-8 * x / wavelength) - 21.1,
                            x => 10**(-(x + 21.1)/2.5) * wavelength * 5.03*10**7 ],
            'jy': [ x => 6.63*10**-4 * x * wavelength, x => 1.51*10**3 * x / wavelength ],
            'janksy': [ x => 6.63*10**-4 * x * wavelength, x => 1.51*10**3 * x / wavelength ],
            'flam': [ x => 1.99*10**-8 * x / wavelength, x => 5.03*10**7 * x * wavelength ],
            'photlam': [ x => x, x => x ]
        }
    }

    const vega = wavelength => {
        // Adjust wavelengths for redshift
        const wavelengths = vegaFlux.wavelength.map(x => x * (1 + document.querySelector('#redshift').value));
        // Handle boundary conditions, return 0 if outside wavelength range
        if (wavelength <= wavelengths.at(0) || wavelength >= wavelengths.at(-1)) {
            return 0;
        }
        // Interpolate to get flux (in flam) at wavelength
        const before = wavelengths.filter(x => x <= wavelength).at(-1);
        const after = wavelengths.filter(x => x > wavelength).at(0);
        const percent = (wavelength - before) / (after - before);
        const below = vegaFlux.flux.at(wavelengths.indexOf(before));
        const above = vegaFlux.flux.at(wavelengths.indexOf(after));
        const resultFlam = below + percent * (above - below);
        return convertUnits(resultFlam, 'flam', 'photlam', wavelength);
    }

    // Get type of both units
    const type = Object.keys(units).filter( type =>
        unitFrom.toLowerCase() in units[type] && unitTo.toLowerCase() in units[type]
    );

    // If units didn't have the same type, throw error
    if (type.length === 0) {
        throw 'Cannot convert from '+unitFrom+' to '+unitTo;
    }

    // If given NaN, return null
    if (isNaN(parseFloat(value))) {
        return null;
    }

    // If units are the same, don't convert
    if (unitFrom === unitTo) {
        return value;
    }

    // Otherwise, convert based on type of unit
    value = parseFloat(value);

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
        if (!wavelength) {
            wavelength = parseFloat(document.querySelector('#wavelength-band').value);
        }
        if (!wavelength) {
            throw 'For flux density conversions, must specify wavelength in Angstroms';
        }
        const valuePhotlam = units.flux[unitFrom.toLowerCase()][1](value);
        return units.flux[unitTo.toLowerCase()][0](valuePhotlam);
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
        min_height: 100,
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
    wavelengthPlot.toolbar.tools.at(-1).tooltips = [['S/N', '$y{0.0}'], ['λ (\u03bcm)', '$x{0.00}']];
    wavelengthPlot.xaxis[0].axis_label = 'Wavelength (\u03bcm)';
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
        min_height: 100,
        sizing_mode: 'scale_width',
        tools: 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, help, hover'
    });
    countsPlot.line({field: 'wavelengths'}, {field: 'total_count_adu'}, {source: source, legend_label: 'Total', line_color: '#CC79A7'});
    countsPlot.line({field: 'wavelengths'}, {field: 'source_count_adu'}, { source: source, legend_label: 'Source', line_color: '#009E73' });
    countsPlot.line({field: 'wavelengths'}, {field: 'background_count_adu'}, { source: source, legend_label: 'Background', line_color: '#0072B2' });
    countsPlot.line({field: 'wavelengths'}, {field: 'read_noise_count_adu'}, { source: source, legend_label: 'Read Noise', line_color: '#E69F00' });
    countsPlot.line({field: 'wavelengths'}, {field: 'dark_current_count_adu'}, { source: source, legend_label: 'Dark Current', line_color: '#000000' });
    countsPlot.line({field: 'wavelengths'}, {field: 'nonlinear_depth_adu'}, { source: source, legend_label: 'Non-linearity', line_color: '#D55E00', line_dash: 'dashed' });
    countsPlot.toolbar.tools.at(-1).tooltips = [['Count (ADU/px)', '$y{0}'], ['Wavelength (\u03bcm)', '$x{0.00}']];
    countsPlot.xaxis[0].axis_label = 'Wavelength (\u03bcm)';
    countsPlot.yaxis[0].axis_label = 'Counts (ADU/px)';
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
        title: 'Wavelength: 0.00 \u03bcm',
        plot_width: 450,
        plot_height: 100,
        min_width: 250,
        min_height: 100,
        sizing_mode: 'scale_width',
        tools: 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, help, hover'
    });
    vsPlot.line({field: 'exposure'}, {field: 'signal_noise_ratio'}, { source: vsSource });
    vsPlot.image_url({
        url: 'src/static/plot_instructions.svg',
        x: 0, y: 0, w: 10, h: 1,
        anchor: 'center'
    });
    vsPlot.output_backend = 'svg';


    // Set callback to change plot size for mobile
    window.addEventListener('resize', () => {
        if (window.innerWidth < 500) {
            wavelengthPlot.height = 300;
            countsPlot.height = 300;
            vsPlot.height = 300;
        }else if (window.innerWidth < 900) {
            wavelengthPlot.height = 200;
            countsPlot.height = 200;
            vsPlot.height = 200;
        } else {
            wavelengthPlot.height = 100;
            countsPlot.height = 100;
            vsPlot.height = 100;
        }
    })


    // Define grid of plots
    const grid = new Bokeh.Plotting.gridplot(
        [[wavelengthPlot], [countsPlot], [vsPlot]], {
        merge_tools: true,
        width: 450,
        height: 100,
        sizing_mode: 'scale_width'
    });
    grid.children[0].toolbar.logo = null;

    Bokeh.Plotting.show(grid, '#output-plots');

    return {resPanelWavelength: resPanelWavelength, vsPlotWavelength: vsPlotWavelength, wavelengthPlot: wavelengthPlot, vsPlot: vsPlot, countsPlot: countsPlot};

}

// Custom handling for reset button on exposure vs. wavelength plot
const resetExposurePlot = () => {
    const exp = source.data['exposure'].filter( value => !Number.isNaN(parseFloat(value)) );
    const ax = wavelengthPlot.y_range;
    if (exp.length > 0){
        ax.end = exp.sort((a, b) => a - b)[Math.floor(exp.length / 2)];
        ax.start = Math.min(...exp) - (ax.end - Math.min(...exp)) * 0.1;
    }
}

// Make API request given query and parameters
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
    const request = await fetch('/api/etc', {
        method: 'POST',
        headers: {'Content-Type': 'text/plain'},
        body: query
    });
    const data = request.status === 200 ? request.json() : {error: request.text()};
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
        'total_count_adu': [],
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

    // Update wavelength unit in results and convert wavelengths to proper unit
    if (data.wavelengths) data.wavelengths = setWavelengthUnit(data.wavelengths);

    // Update ColumnDataSource
    source.data = data;
    source.change.emit();
}

const nonlinearityWarning = () => {
    for(let i = 0; i < source.data.wavelengths.length; i++) {
        if (
            source.data.dark_current_count_adu[i] +
            source.data.source_count_adu[i] +
            source.data.background_count_adu[i] +
            source.data.read_noise_count_adu[i] >=
            source.data.nonlinear_depth_adu[i]
        ) {
            alert('Warning: detector nonlinearity threshold exceeded. See counts plot for more details.');
            break;
        }
    }
}

const updateResults = () => {
    // Get wavelength to use
    const wavelength = resPanelWavelength.location;
    // Set up interpolation
    const idx = source.data['wavelengths'].indexOf( source.data['wavelengths'].filter( x => x <= wavelength ).at(-1) );
    const ratio = (wavelength - source.data['wavelengths'][idx]) / (source.data['wavelengths'][idx+1] - source.data['wavelengths'][idx]);
    // Loop through results, interpolate and display
    for (const id of ['exposure', 'signal-noise-ratio','source-flux','wavelengths','clock-time','efficiency']) {
        const upper = source.data[id.replaceAll('-','_')][idx+1];
        const lower = source.data[id.replaceAll('-','_')][idx];
        document.querySelector('#output-'+id).value = lower + (upper - lower) * ratio;
    }

}

const updateVSPlot = () => {
    // Get wavelength and set corresponding title
    const wavelength = vsPlotWavelength.location;
    vsPlot.title.text = 'Wavelength: ' + wavelength.toPrecision(4) + ' ' + wavelengthUnit.name;
    // Update data for vs. plot
    apiRequest(getQuery(true), getParameters(true)).then( data => {
        // If API request returned errors, format and throw accordingly
        if (Object.keys(data).includes('error')) {
            data.error.then(errorMessage => alert( errorMessage.replaceAll('<br>','\n').replaceAll('&nbsp;',' ')));
            update(true); // Reset calculator
        } else {
            // Update data source with new results
            updateDataSource(vsSource, data);
            // Display / hide instructions conditional on data visibility
            if (vsSource.data['exposure'].filter(x => !isNaN(x)).length == 0 ||
                vsSource.data['signal_noise_ratio'].filter(x => !isNaN(x)).length == 0)
            {
                vsPlot.renderers[1].visible = true;
            } else {
                vsPlot.renderers[1].visible = false;
            }
        }
    });
    // Set axes labels & tooltips according to target
    const target = document.querySelector('#target').value;
    if (target === 'exposure') {
        vsPlot.renderers[0].glyph.x = {field: 'signal_noise_ratio'};
        vsPlot.renderers[0].glyph.y = {field: 'exposure'};
        vsPlot.toolbar.tools.at(-1).tooltips = [['Exp (s)', '$y{0}'], ['S/N', '$x{0.0}']];
        vsPlot.xaxis[0].axis_label = 'SNR';
        vsPlot.yaxis[0].axis_label = 'Exposure (s)';
    } else if (target === 'signal_noise_ratio') {
        vsPlot.renderers[0].glyph.x = {field: 'exposure'};
        vsPlot.renderers[0].glyph.y = {field: 'signal_noise_ratio'};
        vsPlot.toolbar.tools.at(-1).tooltips = [['S/N', '$y{0.0}'], ['Exp (s)', '$x{0}']];
        vsPlot.xaxis[0].axis_label = 'Exposure (s)';
        vsPlot.yaxis[0].axis_label = 'SNR';
    }


}

const updateUI = (parameters, instrumentChanged) => {

    // Loop through all inputs in app
    document.querySelectorAll('input-select, input-spin, input-slider').forEach( input => {
        const name = input.id.replaceAll('-','_');
        // If id is not parameter, parameter-unit, parameter-min, or parameter-max, then hide inactive element
        if (!(name in parameters || name.replace('_unit','') in parameters ||
            name.replace('_min','') in parameters || name.replace('_max','') in parameters ||
            name.replace('_width','') in parameters || name.replace('_length','') in parameters))
        {
            input.classList.remove('visible');

        } else if (name.startsWith('slit_') && String(document.querySelector('#slit').value).toLowerCase() !== 'custom') {
            input.classList.remove('visible');
        } else if (!name.endsWith('unit') && !name.endsWith('min') && !name.endsWith('max') && !name.endsWith('width') && !name.endsWith('length')) {
            // Otherwise, get value from parameters
            let value = parameters[name].value;

            // Before changing input, disable callbacks for change events
            guiInactive = true;

            // If needed, convert value to appropriate unit
            if (document.querySelector('#'+input.id+'-unit')) {
                value = convertUnits(value, parameters[name].unit, document.querySelector('#'+input.id+'-unit').value);
                input.unit = parameters[name].unit;
            }
            // If min and max are unset, set to defaults of 0 and 2 * value
            if (document.querySelector('#'+input.id+'-min') && input.min === null) {
                document.querySelector('#'+input.id+'-min').value = 0;
                input.min = 0;
            }
            if (document.querySelector('#'+input.id+'-max') && input.max === null) {
                document.querySelector('#'+input.id+'-max').value = 2 * value;
                input.max = 2 * value;
            }
            // If available, set options for select
            if (parameters[name].options) {
                input.options = parameters[name].options;
            }
            // In the case of custom slit, set width and height inputs to value
            if (name === 'slit' &&
                input.options.filter(o => o.value === 'Custom').length > 0 &&
                ( ( input.value === 'Custom' && !instrumentChanged ) ||
                input.options.filter(o => String(o.value) === String(value)).length === 0 ))
            {
                document.querySelector('#slit-width').value = value[0];
                document.querySelector('#slit-length').value = value[1];
                value = 'Custom';
                document.querySelector('#slit-width').classList.add('visible');
                document.querySelector('#slit-length').classList.add('visible');
            }

            // Set value
            input.value = value;
            guiInactive = false;

            input.classList.add('visible');
        } else {
            input.classList.add('visible');
        }
    });
    document.querySelector('input-file').classList.add('visible');

    // Set input row visibility according to children
    document.querySelectorAll('.input-row').forEach( row => {
        // If any child is visible, set row to visible
        const visible = [...row.children].reduce( (prev, curr) =>
            [...curr.classList].includes('visible') ? true : prev,
        false);

        if (visible) {
            row.classList.add('visible');
        } else {
            row.classList.remove('visible');
        }
    });

    // Update instrument name
    guiInactive = true;
    document.querySelector('instrument-menu').value = parameters.name.value;
    guiInactive=  false;

    // Update first plot according to target
    const target = document.querySelector('#target').value;
    // Define precision for plot tooltips
    let precision = '0';
    if (wavelengthUnit.value === 'micron') {
        precision = '0.00';
    }
    if (target === 'exposure') {
        wavelengthPlot.renderers[0].glyph.y = {field: 'exposure'};
        wavelengthPlot.toolbar.tools.at(-1).tooltips = [['Exp (s)', '$y{0}'], ['\u03bb (' + wavelengthUnit.name + ')', '$x{' + precision + '}']];
        wavelengthPlot.yaxis[0].axis_label = 'Exposure (s)';
        wavelengthPlot.title.text = 'Exposure';
        wavelengthPlot.renderers[0].visible = true;
        wavelengthPlot.renderers[1].visible = false;
        wavelengthPlot.js_event_callbacks = {
            ...wavelengthPlot.js_event_callbacks,
            reset: [new Bokeh.CustomJS({ code: 'resetExposurePlot();' })]
        };
        wavelengthPlot.reset.emit();
    } else if (target === 'signal_noise_ratio') {
        wavelengthPlot.renderers[0].glyph.y = {field: 'signal_noise_ratio'};
        wavelengthPlot.toolbar.tools.at(-1).tooltips = [['S/N', '$y{0.0}'], ['\u03bb (' + wavelengthUnit.name + ')', '$x{' + precision + '}']];
        wavelengthPlot.yaxis[0].axis_label = 'SNR';
        wavelengthPlot.title.text = 'Signal to Noise Ratio';
        wavelengthPlot.renderers[0].visible = false;
        wavelengthPlot.renderers[1].visible = true;
        wavelengthPlot.js_event_callbacks = {
            ...wavelengthPlot.js_event_callbacks,
            reset: []
        };
    }
}

const update = (reset, load, instrumentChanged) => {
    // If reset is true, don't supply parameters to API call
    let parameters = {};
    if (load) {
        // Load saved state from cookies
        const cookies = document.cookie.split(';');
        for (const i in cookies) {
            const cookie = cookies[i].trim().split('=');
            if (cookie[0] === 'etcparameters'){
                parameters = JSON.parse(cookie[1]);
            }
        }
        // Load saved state from local storage
        if (window.localStorage.getItem('etcTypeDefinition')) {
            guiInactive = true;
            document.querySelector('#file-upload').file = window.localStorage.getItem('etcTypeDefinition');
            guiInactive = false;
            parameters.typeb64 = document.querySelector('#file-upload').file;
        }
        // Load query parameters
        let queryString = window.location.search;
        queryString.replace(/[^a-zA-Z0-9\.\=\[\]\-()&+_,]/,''); // Filter characters by whitelist
        new URLSearchParams(queryString).forEach( (val, key) => parameters[key] = val );
    } else if (reset) {
        // Reset calculator to defaults, erase cookies and local storage, send parameters={}
        document.cookie = 'etcparameters={}; expires=' + new Date();
        window.localStorage.clear();
        document.querySelector('#file-upload').removeAttribute('file');
    } else if (instrumentChanged) {
        // TODO -- don't reset atmosphere, exposure, source parameters while changing instrument
        parameters.name = document.querySelector('instrument-menu').value.toUpperCase();
    } else {
        // Get parameters from GUI
        parameters = getParameters(false);
    }
    // Display loading symbols on output
    document.querySelectorAll('.panel.output').forEach(el => el.classList.add('loading'));
    // Get results from ETC, update ui and data
    apiRequest(getQuery(false), parameters).then( data => {
        // If API request returned errors, format and throw accordingly
        if (Object.keys(data).includes('error')) {
            data.error.then(errorMessage => alert( errorMessage.replaceAll('<br>','\n').replaceAll('&nbsp;',' ')));
            update(true); // Reset calculator
        } else {
            // Update data sources and UI
            updateDataSource(source, data);
            updateUI(data.parameters, instrumentChanged);
            // Change results to reflect new data
            updateResults();
            // Get vs. data and update plot
            updateVSPlot();
            // Done updating document, remove loading symbols
            document.querySelectorAll('.panel.output.loading').forEach(el => el.classList.remove('loading'));
            // If counts exceed nonlinearity threshold, trigger warning
            // TODO -- get Sherry's input on this
            //nonlinearityWarning(data);
        }
    // On error, display to user
    }).catch( error => {
        alert('Error:\n'+error);
        update(true); // Reset calculator
    });

}

const getQuery = (isForVSPlot) => {
    let query = 'return=[exposure,signal_noise_ratio'
    if (!isForVSPlot) {
        query += ',source_count_adu,read_noise_count_adu,total_count_adu,clock_time,' +
                'wavelengths,background_count_adu,dark_current_count_adu,' +
                'efficiency,source_flux,nonlinear_depth_adu,parameters';
    }
    query += ']';
    return query;
}

const getParameters = isForVSPlot => {
    const options = [
        'exposure', 'signal_noise_ratio', 'dithers', 'repeats', 'coadds', 'reads',
        'type', 'flux', 'wavelength_band', 'redshift', 'index', 'temperature', 'width',
        'mode', 'slit', 'binning', 'dichroic', 'grating', 'grism', 'filter', 'seeing', 'airmass',
        'water_vapor', 'target' // Target is last because it resets snr/exp to default
    ];
    // Set instrument name first so that all instrument-specific parameters will be applied
    const parameters = {};
    if (document.querySelector('instrument-menu').value) {
        parameters.name = document.querySelector('instrument-menu').value.toUpperCase();
    }

    // If custom source SED uploaded, add to query
    const customSource = document.querySelector('#file-upload').file;

    if (customSource) {
        parameters['typeb64'] = customSource;
        const filename = customSource.split(',')[0];
        // If SED filename not in list of source types, it was just added
        if (document.querySelector('#type').options.filter( opt => opt.name === filename.split('.')[0] ).length === 0) {
            // In that case, remove source type from query in order to automatically set source to new type
            options.splice(options.indexOf('type'), 1);
        }
    }

    for (parameter of options) {
        const id = '#'+parameter.replaceAll('_','-');
        const element = document.querySelector(id);

        if (!!element && element.classList.contains('visible') && element.value){

            const unit = !!document.querySelector(id+'-unit') ? document.querySelector(id+'-unit').value : '';

            // For vs. plot, get range of exp/snr from min and max elements
            if (isForVSPlot && (id==='#exposure' || id==='#signal-noise-ratio')){
                const start = parseFloat(document.querySelector(id+'-min').value);
                const stop = parseFloat(document.querySelector(id+'-max').value);
                const step = (stop - start) / (25-1); // Hard-coded value of 25 points
                const list = Array(25).fill(start).map((x, i) => x + i * step);
                parameters[parameter] = list.map(x => x+unit);

            // For custom slit, get values from width and length inputs
            } else if (id==='#slit' && element.value === 'Custom') {
                const width = document.querySelector('#slit-width').value;
                const length = document.querySelector('#slit-length').value;
                parameters[parameter] = width + unit + ',' + length + unit;

            // Otherwise, get value from element
            } else {
                parameters[parameter] = element.value + unit;
            }
        }
    }

    // Save current parameters as cookie, to resume session on future site load
    if (!isForVSPlot) {
        const exp_date = new Date( new Date().getTime() + 48 * 60 * 60 * 1000 );  // Add 48 hours to current date

        // Remove base 64 encoded source type definition from parameter string, if present
        const parameterString = JSON.stringify(Object.fromEntries(Object.entries(parameters).filter( ([key,val]) => key !== 'typeb64' )));
        document.cookie = 'etcparameters=' + parameterString + '; expires=' + exp_date.toUTCString() + '; SameSite=Strict;';

        // If base 64 encoded source type definition was present, save in local storage instead of as cookie (too big for cookie)
        if (parameters['typeb64']) {
            window.localStorage.setItem('etcTypeDefinition',parameters.typeb64);
        }
    } else {
        // For vs. plot, specify wavelength
        parameters.wavelengths = [vsPlotWavelength.location + wavelengthUnit.value];
    }
    return parameters;
}

const setWavelengthUnit = wavelengths => {
    // If instrument is IR, use micrometers
    let unit = { value: 'micron', name: '\u03bcm' }
    // If instrument is optical, use angstroms
    if (wavelengths[0] <= 6000) {
        unit = { value: 'angstrom', name: '\u212b' }
    }

    // If the unit has changed, update plots and results appropriately
    if (unit.value !== wavelengthUnit.value) {

        // Define precision for plot tooltips
        let precision = '0';
        if (unit.value === 'micron') {
            precision = '0.00';
        }

        // Set unit for results panel
        document.querySelector('#output-wavelengths').unit = unit.name;
        // Set unit for wavelength plot
        wavelengthPlot.xaxis[0].axis_label = 'Wavelength (' + unit.name + ')';
        wavelengthPlot.toolbar.tools.at(-1).tooltips = [
            wavelengthPlot.toolbar.tools.at(-1).tooltips[0],
            ['\u03bb (' + unit.name + ')', '$x{' + precision + '}']
        ];
        // Set unit for counts plot
        countsPlot.xaxis[0].axis_label = 'Wavelength (' + unit.name + ')';
        countsPlot.toolbar.tools.at(-1).tooltips = [
            countsPlot.toolbar.tools.at(-1).tooltips[0],
            ['Wavelength (' + unit.name + ')', '$x{' + precision + '}']
        ];

        // Convert unit for plot wavelength markers
        vsPlotWavelength.location = convertUnits(vsPlotWavelength.location, wavelengthUnit.value, unit.value);
        resPanelWavelength.location = convertUnits(resPanelWavelength.location, wavelengthUnit.value, unit.value);

        // Save unit changes to greater scope
        wavelengthUnit = unit;
    }

    // Convert data to proper unit
    wavelengths = wavelengths.map( x => convertUnits(x, 'angstrom', unit.value) );
    return wavelengths;

}


// Called when page loads
const setup = async () => {
    // Get data for flux of vega from async call
    vegaFlux = await vegaFlux;

    // Initialize wavelength unit to use in plots and results
    wavelengthUnit = { value: 'micron', name: '\u03bcm' };

    // Define instrument-menu click behavior
    document.querySelector('instrument-menu').addEventListener('change', () => {
        if (!guiInactive) {
            update(false, false, true)
        }
    });

    // Define reset button click handling
    document.querySelector('button#reset').addEventListener('click', () => {
        update(true);
    });

    // Define mobile collapse / expand behavior
    document.querySelectorAll('div.section-title').forEach( (el) => {

        // Initialize max height to allow CSS animations
        if (window.innerWidth < 900) {
            el.closest('div.panel').style.maxHeight = window.getComputedStyle(el.closest('div.panel')).height;
        }

        // Set resize callback to initialize max height for desktop/mobile changes
        window.addEventListener('resize', event => {
            if (!event.isTrusted) return; // Only allow window generated events, i.e. width changes

            if (window.innerWidth < 900) {
                el.closest('div.panel').classList.remove('open');
                el.closest('div.panel').style.maxHeight = window.getComputedStyle(el.closest('div.panel')).height;
            } else {
                el.closest('div.panel').style.maxHeight = '999vh';
            }
        });
        
        el.addEventListener('click', () => {
            // For tablet/mobile only
            if (window.innerWidth < 900) {

                // Get anscestor panel
                const toggle = el.closest('div.panel');

                // On click, toggle css .open class
                if (toggle.classList.contains('open')) {
                    const paddingTop = parseFloat(window.getComputedStyle(toggle).paddingTop);
                    const paddingBottom = parseFloat(window.getComputedStyle(toggle).paddingBottom);
                    const titleHeight = parseFloat(window.getComputedStyle(toggle.querySelector('.section-title')).height);
                    toggle.style.maxHeight = titleHeight + paddingTop + paddingBottom + 'px';
                    window.setTimeout( () => toggle.classList.remove('open'), 300);
                } else {
                    toggle.style.maxHeight = '999vh';
                    toggle.classList.add('open');
                }
            }

        });
    });

    // Read in mouseover text file
    fetch('src/static/mouseover_text.json').then(response =>
        response.json() ).then( data => {
            // Add tooltips to appropriate elements based on file
            for (const [name, text] of Object.entries(data)) {
                const el = document.getElementById(name);
                if (el) {
                    el.info = text.trim();
                }
            };
        }).catch(error => console.log(error));

    // Read in instructions text file
    fetch('src/static/gui_instructions.txt').then(response =>
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
    ({resPanelWavelength, vsPlotWavelength, wavelengthPlot, vsPlot, countsPlot} = createPlots(source, vsSource));
    // Update inputs and outputs with values from API
    update(false, true);


    // Define callbacks on value changes for inputs
    document.querySelectorAll('input-select, input-spin, input-slider, input-file').forEach( input => {
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
                if (!guiInactive) {
                    guiInactive = true;
                    number.min = input.value;
                    guiInactive = false;
                    updateVSPlot();
                } else {
                    number.min = input.value;
                }
            });
        // If maximum, set value for corresponding element
        } else if (input.id.endsWith('max')) {
            const number = document.querySelector('#'+input.id.replace('-max',''));
            input.addEventListener('change', () => {
                if (!guiInactive) {
                    guiInactive = true;
                    number.max = input.value;
                    guiInactive = false;
                    updateVSPlot();
                } else {
                    number.max = input.value;
                }
            });
        // Otherwise, call update() to make API call w/ changed value and display results
        } else {
            input.addEventListener('change', () => {if (!guiInactive) { update() } });
        }
    });

    // Prevent default file drag-and-drop behavior, in case user misses file upload
    window.addEventListener("dragover", e=> {
        e.stopPropagation();
        e.preventDefault();
        e.dataTransfer.dropEffect = 'none';
    },false);
    window.addEventListener("drop", e=> {
        e.stopPropagation();
        e.preventDefault();
    },false);


    // Define download button click handling
    document.querySelector('button#download').addEventListener('click', () => {
        const table_to_csv = (source) => {
            // Remove 'parameters' column from data
            const { parameters, ...data } = source.data;
            const columns = Object.keys(data);
            const nrows = source.get_length();
            const lines = [columns.join(',')];
            for (let i = 0; i < nrows; i++) {
                let row = [];
                for (let j = 0; j < columns.length; j++) {
                    const column = columns[j];
                    row.push(data[column][i].toString());
                }
                lines.push(row.join(','));
            }
            return lines.join('\n').concat('\n');
        }

        const filename = 'etc_results.csv';
        const filetext = table_to_csv(source);
        const blob = new Blob([filetext], { type: 'text/csv;charset=utf-8;' });

        //for IE
        if (navigator.msSaveBlob) {
            navigator.msSaveBlob(blob, filename);
        } else {
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.target = '_blank';
            link.style.visibility = 'hidden';
            link.dispatchEvent(new MouseEvent('click'));
        }
    });


};

// For production, avoid filling console with warnings whenever empty plot is generated
Bokeh.set_log_level('error');

// Once content is loaded, call setup function to initialize page functionality
window.addEventListener('DOMContentLoaded', setup);

// For incorporation into iframe, dispatch resize events when page width or height changes
const resizeObserver = new ResizeObserver(() => window.dispatchEvent(new Event('resize')));
resizeObserver.observe(document.querySelector('html'));
