window.customElements.define('input-file', class extends HTMLElement {

    static get observedAttributes() {
        return ['info', 'files'];
    }

    get info() { return this.getAttribute('info'); }
    get files() { return this.input.files; }

    set info(val) {
        this.setAttribute('info', val);
        this.label.info = val;
    }

    set files(val) {
        if (typeof val === 'object' && val instanceof FileList) {
            this.input.files = val;
        }
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (newValue !== oldValue) {
            if (name === 'info') { this.info = newValue; }
            if (name === 'files') { this.files = newValue; }
        }
    }


    constructor() {

        super();

        this.attachShadow({mode: 'open'});

        this.shadowRoot.innerHTML = '<input-label><slot></slot>:</input-label>' +
                                    '<input type="file" accept=".txt,.fits" style="width: 100%">'
        
        this.label = this.shadowRoot.firstElementChild;
        this.input = this.shadowRoot.lastElementChild;

        // Add event listener to file input
        this.input.addEventListener('change', () => {
            // Signal file changed for any event listeners attached to this
            this.dispatchEvent(new Event('change'));
        });
        
    }

});