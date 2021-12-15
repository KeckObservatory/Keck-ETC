
// Make API request to get info
const apiRequest = async (parameters) => {
    // TODO -- finish method
    let query = '?return=[wavelengths,exposure,signal_noise_ratio,source_count_adu,' +
                'background_count_adu,read_noise_count_adu,dark_current_count_adu,' +
                'integration_time,source_flux,nonlinear_depth_adu]';
    for (const [key, value] of Object.entries(parameters)){
        query += '&'+key+'='+value;
    }
    const request = await fetch('http://vm-internship:8080'+query);
    const data = request.status === 200 ? request.json() : {};
    return data;
}


const createDataSources = () => {
    // Create source
    const source = new Bokeh.ColumnDataSource({ data: { 
        'wavelengths': [0,1],
        'exposure': [0,1],
        'source_count_adu': [0,1],
        'background_count_adu': [0,1],
        'read_noise_count_adu': [0,1],
        'dark_current_count_adu': [0,1],
        'signal_noise_ratio': [0,1],
        'nonlinear_depth_adu': [0,1],
        'integration_time': [0,1],
        'source_flux': [0,1]
    }});

    const vsSource = new Bokeh.ColumnDataSource({ data: {
        'x': [0, 1],
        'y': [0, 1]
    }});

    return {source: source, vsSource: vsSource};
}

const updateDataSources = (data) => {
    // Format data so that every column is the same length
    for (const [key, value] of Object.entries(data)) {
        if (typeof value === 'number') {
            data[key] = new Array(data.wavelengths.length).fill(value);
        } else if (value.length === 1 && typeof value[0] === 'object') {
            data[key] = value[0];
        } else if (value.length === 1) {
            data[key] = new Array(data.wavelengths.length).fill(value[0]);
        }
    }
    // Update ColumnDataSource
    source.data = data;
    console.log(source);
    source.change.emit();
}

// Define Bokeh source and plots
const createPlots = (source, vsSource) => {
    
    // Create vertical lines for marking wavelengths
    const wavelength = new Bokeh.Span({
        location: 0.5,
        dimension: 'height',
        line_color: 'black',
        line_dash: 'dashed'
    });
    const vsPlotWavelength = new Bokeh.Span({
        location: 0.5,
        dimension: 'height',
        line_color: '#333',
        line_dash: 'solid'
    });
    const callbacks = { 
        mousemove: [new Bokeh.CustomJS({ args: {w: wavelength}, code: 'w.location=cb_obj.x; updateResults(cb_obj.x)' })],
        tap: [new Bokeh.CustomJS({ args: {w: vsPlotWavelength}, code: 'w.location=cb_obj.x; updateVSPlot(cb_obj.x)' })]
    };



    // Define first plot, snr/exp vs. wavelength
    const wavelengthPlot = new Bokeh.Plotting.figure({
        name: 'plot',
        title: 'Signal to Noise Ratio',
        plot_width: 450,
        plot_height: 100,
        min_width: 250,
        sizing_mode: 'scale_width',
        tooltips: [('S/N', '$y{0.0}'), ('λ (nm)', '$x{0}')],
        tools: 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, hover, help'
    });
    wavelengthPlot.scatter({field: 'wavelengths'}, {field: 'signal_noise_ratio'}, {
        source: source, 
        alpha: 0.5, 
        size: 6, 
        legend_label: '\u00A0'
    });
    const line = wavelengthPlot.line({field: 'wavelengths'}, {field: 'signal_noise_ratio'}, {
        source: source, 
        legend_label: ''
    });
    wavelengthPlot.xaxis[0].axis_label = 'Wavelength (nm)';
    wavelengthPlot.yaxis[0].axis_label = 'Signal to Noise Ratio';
    line.visible = false;  // Initially start hidden
    wavelengthPlot.output_backend = 'svg';
    wavelengthPlot.legend.label_height=10;
    wavelengthPlot.legend.label_width=10;
    wavelengthPlot.legend.label_text_font_size = '10px';
    wavelengthPlot.legend.click_policy = 'hide';
    wavelengthPlot.add_layout(wavelength);
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
        tools: 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, hover, help'
    });
    countsPlot.line({field: 'wavelengths'}, {field: 'source_count_adu'}, { source: source, legend_label: 'Source', line_color: '#009E73' });
    countsPlot.line({field: 'wavelengths'}, {field: 'background_count_adu'}, { source: source, legend_label: 'Background', line_color: '#0072B2' });
    countsPlot.line({field: 'wavelengths'}, {field: 'read_noise_count_adu'}, { source: source, legend_label: 'Read Noise', line_color: '#CC79A7' });
    countsPlot.line({field: 'wavelengths'}, {field: 'dark_current_count_adu'}, { source: source, legend_label: 'Dark Current', line_color: '#000000' });
    countsPlot.line({field: 'wavelengths'}, {field: 'nonlinear_depth_adu'}, { source: source, legend_label: 'Non-linearity', line_color: '#D55E00', line_dash: 'dashed' });
    countsPlot.xaxis[0].axis_label = 'wavelengths (nm)'
    countsPlot.yaxis[0].axis_label = 'Counts (ADU/px)'
    countsPlot.legend.label_height = 10;
    countsPlot.legend.label_width = 10;
    countsPlot.legend.label_text_font_size = '10px';
    countsPlot.legend.click_policy = 'hide';
    countsPlot.legend.spacing = 0;
    countsPlot.output_backend = 'svg';
    countsPlot.add_layout(wavelength);
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
        tools: 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, hover, help'
    });
    vsPlot.line({field: 'x'}, {field: 'y'}, { source: vsSource });
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

    return {wavelength: wavelength, wavelengthPlot: wavelengthPlot, vsPlot: vsPlot};

}

const updateResults = (wavelength) => {
    console.log(wavelength);
}

const updateVSPlot = (wavelength) => {
    vsPlot.title.text = 'Wavelength: ' + wavelength.toFixed(0) + 'nm';
}

const getParameters = () => {
    const options = [
        'target', 'exposure', 'signal_noise_ratio', 'dithers', 'repeats', 'coadds', 'reads',
        'type', 'flux', 'wavelength_band', 'redshift', 'index', 'temperature', 'line_width',
        'mode', 'slit', 'binning', 'grating', 'grism',
        'seeing', 'airmass', 'water_vapor'
    ];
    const parameters = {};

    for (parameter of options) {
        const id = '#'+parameter.replace('_','-');
        const element = document.querySelector(id);
        if (!!element && !element.classList.contains('hidden')){
            const unit = !!document.querySelector(id+'-unit') ? document.querySelector(id+'-unit').value : '';
            parameters[parameter] = element.value + unit;
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
    document.querySelectorAll('div.section-title').forEach( (el) => {
        el.addEventListener('click', (event) => {
            // On click, toggle css .open class
            if (el.parentElement.classList.contains('open')) {
                el.parentElement.classList.remove('open');
            } else {
                el.parentElement.classList.add('open');
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


        // Define ColumnDataSource, then get values from API
        ({source, vsSource} = createDataSources());
        apiRequest(getParameters()).then(data=>updateDataSources(data));
        ({wavelengthPlot, vsPlot} = createPlots(source, vsSource));

};



window.addEventListener('DOMContentLoaded', setup);