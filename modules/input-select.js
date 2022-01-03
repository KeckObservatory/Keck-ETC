window.customElements.define('input-select', class extends HTMLElement {

    static get observedAttributes() {
        return ['label', 'info', 'value', 'options'];
    }

    get info() { return this.getAttribute('info'); }
    get label() { return this.getAttribute('label'); }
    get value() { return this.getAttribute('value'); }
    
    get options() {
        return Array.from(this.select.children).map( child => ({
            name: child.textContent,
            value: child.value
        }));
    }

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
        const options = this.options.map( opt => opt.value );
        if (options.includes(String(val))) {
            const event = new Event('change');
            event.oldValue = this.value;
            event.newValue = val;
            if (event.newValue !== event.oldValue) {
                this.setAttribute('value', val);
                this.select.value = val;
                this.dispatchEvent(event);
            }
        } else if (options.length > 0){
            throw 'Value ' + val + ' is not a valid option';
        }
    }

    set options(val) {
        // Remove current options
        while (this.select.firstChild) { this.select.removeChild(this.select.firstChild) };
        // Add options based on input
        val.forEach( option => {
            const el = document.createElement('option');
            el.value = option.value;
            if ('name' in option) {
                el.innerText = option.name;
            } else if (option.value instanceof Array) {
                el.innerText = option.value.join(' x ');
            } else {
                el.innerText = option.value;
            }
            this.select.appendChild(el);
        });
    }

    connectedCallback() {
        // If no label given, set to whitespace for spacing
        if (!this.label && !this.info) {
            this.label = '\xa0'
        }
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (newValue !== oldValue) {
            if (name === 'info') { this.info = newValue; }
            if (name === 'label') { this.label = newValue; }
            if (name === 'value') { this.value = newValue; }
            if (name === 'options') { this.options = newValue; }
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
            if (!this.value) this.value = this.select.value;
        });
        
        this.labelElement = this.shadowRoot.firstElementChild;

        // Add event listener to input
        this.select.addEventListener('change', () => {
            // Update value when select value changes
            this.value = this.select.value;
        });

        // Add CSS to shadow DOM
        const link = document.createElement('link');
        link.rel = 'stylesheet'; 
        link.type = 'text/css';
        link.href = 'modules/input-select.css';
        this.shadowRoot.append(link)
    }

});