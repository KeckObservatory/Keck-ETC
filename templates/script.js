
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

};