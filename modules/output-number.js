window.customElements.define('output-number', class extends HTMLElement {

    static get observedAttributes() {
        return ['value', 'unit'];
    }

    get value() { return parseFloat(this.getAttribute('value')); }
    get unit() { return this.getAttribute('unit'); }

    set unit(val) {
        if ((typeof val === 'string' || val instanceof String) && val.length <= 5) {
            this.setAttribute('unit', val);
            this.setContent();
        }
    }

    set value(val) {
        // Ensure positive float value or NaN
        this.setAttribute('value', Math.abs(parseFloat(val)));
        this.setContent();
    }

    connectedCallback() {
        // Set default value to NaN and default unit to ' '
        if (!this.value) {
            this.value = NaN;
        }
        if (!this.unit) {
            this.unit = ' ';
        }

    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (newValue !== oldValue) {
            if (name === 'value') { this.value = newValue; }
            if (name === 'unit') {this.unit = newValue; }
        }
    }


    constructor() {

        super();

        this.attachShadow({mode: 'open'});

        this.shadowRoot.innerHTML = '<div>' +
                                    '   <p></p>' +
                                    '   <label><slot></slot></label>' +
                                    '</div>'
        
        this.output = this.shadowRoot.querySelector('p');

        // Add CSS to shadow DOM
        const link = document.createElement('link');
        link.rel = 'stylesheet'; 
        link.type = 'text/css';
        link.href = 'modules/output-number.css';
        this.shadowRoot.append(link)
    }


    setContent() {
        // Format value so that "value unit" <= 10 characters

        // If NaN, return "---" in place of value
        if (isNaN(this.value)) {
            this.output.textContent = '--- ' + this.unit;
            return;
        }

        //let outputText = String(this.value);
        // Return "value unit" if length <= 10 chars
        if ((this.value+this.unit).length < 10) {
            this.output.textContent = this.value + ' ' + this.unit;
            return;
        }

        const numChars = 7 - this.unit.length

        // If number is too big or too small, use scientific notation
        if (this.value >= 10**numChars || this.value <= 10**(1-numChars)) {
            const expDigits = this.value.toExponential(0).split(/[+-]/).at(-1).length;
            const numDecimals = Math.max(numChars - expDigits - 2, 0);
            const exponential = this.value.toExponential(numDecimals);
            this.output.textContent = exponential + ' ' + this.unit;
            return;
        }

        // Otherwise, trim number to correct number of decimal places
        const numDigits = Math.log(parseInt(this.value)) * Math.LOG10E + 1 | 0;
        this.output.textContent = this.value.toFixed(numChars - numDigits) + ' ' + this.unit;

    }


});