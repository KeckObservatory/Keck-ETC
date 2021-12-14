
// Make API request to get info
const apiRequest = (parameters) => {
    // TODO -- finish method
    console.log('Setting '+JSON.stringify(parameters))
}


// Define Bokeh source and plots
const createPlots = () => {
    // Create source
    var source = new Bokeh.ColumnDataSource({ data: { 
            'wavelengths': [0,1],
            'exposure': [0,1],
            'source': [0,1],
            'background': [0,1],
            'read_noise': [0,1],
            'dark_current': [0,1],
            'snr': [0,1],
            'nonlinear': [0,1],
            'integration': [0,1],
            'flux': [0,1]
     } });

    // Define first plot, snr/exp vs. wavelength
    const wavelengthPlot = new Bokeh.Plotting.figure({
        name: 'plot',
        title: 'Signal to Noise Ratio',
        plot_width: 400,
        plot_height: 100,
        sizing_mode: 'scale_width',
        tooltips: [('S/N', '$y{0.0}'), ('λ (nm)', '$x{0}')],
        tools: 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, hover, help'
    });
    wavelengthPlot.xaxis.axis_label = 'Wavelength (nm)';
    wavelengthPlot.yaxis.axis_label = 'Signal to Noise Ratio';
    wavelengthPlot.scatter({field: 'wavelengths'}, {field: 'snr'}, {
        source: source, 
        alpha: 0.5, 
        size: 6, 
        legend_label: '\u00A0'
    });
    const line = wavelengthPlot.line({field: 'wavelengths'}, {field: 'snr'}, {
        source: source, 
        legend_label: ''
    });
    const wavelength = new Bokeh.Span({
        location: 0.5,
        dimension: 'height',
        line_color: 'black',
        line_dash: 'dashed'
    });
    wavelengthPlot.add_layout(wavelength);
    line.visible = false;  // Initially start hidden
    wavelengthPlot.output_backend = 'svg';
    wavelengthPlot.legend.label_height=10;
    wavelengthPlot.legend.label_width=10;
    wavelengthPlot.legend.label_text_font_size = '10px';
    wavelengthPlot.legend.click_policy = 'hide';
    // Add event listener for mousemove on plot
    wavelengthPlot.js_event_callbacks = { mousemove: [new Bokeh.CustomJS({
        args: {w: wavelength},
        code: 'w.location = cb_obj.x'
    })]};


    const plot2 = new Bokeh.Plotting.figure({
        title: "Second Plot",
        plot_width: 400,
        plot_height: 100,
        sizing_mode: 'scale_width',
        tools: 'pan, box_zoom, zoom_in, zoom_out, wheel_zoom, undo, redo, reset, save, hover, help'
    });
    plot2.line({field: 'wavelengths'}, {field: 'exposure'}, {
        source: source,
        legend_label: 'bye',
        line_color: '#CC79A7'
    });

    const grid = new Bokeh.Plotting.gridplot([[wavelengthPlot],[plot2]], {
        merge_tools: true,
        width: 400,
        height: 100,
        sizing_mode: 'scale_width'
    });

    Bokeh.Plotting.show(grid, '#output-plots');
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
        apiRequest({});
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


    createPlots();
      

};

window.addEventListener('DOMContentLoaded', setup);