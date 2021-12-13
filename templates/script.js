
// Make API request to get info
const apiRequest = (parameters) => {
    // TODO -- finish method
    console.log('Setting '+JSON.stringify(parameters))
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
    document.querySelector('button.reset').addEventListener('click', event => {
        apiRequest({});
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

};

window.addEventListener('DOMContentLoaded', setup);