window.customElements.define('input-select', class extends HTMLElement {

    static get observedAttributes() {
        return ['label', 'info', 'value'];
    }

    get info() { return this.getAttribute('info'); }
    get label() { return this.getAttribute('label'); }
    get value() { return this.select.value; }

    set info(val) {
        this.setAttribute('info', val);
        this.labelElement.info = val;
    }

    set label(val) {
        if (val && val.trim() && !val.endsWith(':')) {
            val += ':';
        }
        this.setAttribute('label', val);
        this.labelElement.textContent = val;
    }

    set value(val) {
        const options = Array.from(a.select.options).map( o => o.value);
        if (options.includes(val)) {
            this.select.value = val;
        }
    }

    connectedCallback() {
        if (!this.label && !this.info) {
            this.label = '\xa0'  // Set to whitespace for spacing
        }
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (newValue !== oldValue) {
            if (name === 'info') { this.info = newValue; }
            if (name === 'label') { this.label = newValue; }
            if (name === 'value') { this.value = newValue; }
        }
    }


    constructor() {

        super();

        this.attachShadow({mode: 'open'});

        this.shadowRoot.innerHTML = '<input-label></input-label>' +
                                    '<select></select>' +
                                    '<slot></slot>'

        // Because slot doesn't work inside <select> elements,
        // move <options> from <slot> to the inside of <select>
        this.select = this.shadowRoot.querySelector( 'select' );  
        this.shadowRoot.addEventListener( 'slotchange', event => {      
            let node = this.querySelector( 'option' );
            node && this.select.append( node );
        });
        
        this.labelElement = this.shadowRoot.firstElementChild;

        // Add CSS to shadow DOM
        const link = document.createElement('link');
        link.rel = 'stylesheet'; 
        link.type = 'text/css';
        link.href = 'modules/input-select.css';
        this.shadowRoot.append(link)
    }

});