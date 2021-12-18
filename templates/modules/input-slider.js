window.customElements.define('input-slider', class extends HTMLElement {


    static get observedAttributes() {
        return ['min', 'max', 'value', 'unit', 'info'];
    }

    get info() { return this.getAttribute('info'); }
    get min() { return this.getAttribute('min'); }
    get max() { return this.getAttribute('max'); }
    get value() { return this.getAttribute('value'); }
    get unit() { return this.getAttribute('unit'); }

    set info(val) {
        this.setAttribute('info', val);
        this.label.info = val;
    }

    set min(val) {
        if (!isNaN(val)) {
            val = parseFloat(val);
            if (!this.max || val <= this.max) {
                this.setAttribute('min', val);
                this.slider.min = val;
                this.slider.step = (this.max - this.min) / 100;
                if (this.value < val) {
                    this.value = val;
                }
            }
        }
    }

    set max(val) {
        if (!isNaN(val)) {
            val = parseFloat(val);
            if (!this.min || val >= this.min) {
                this.setAttribute('max', val);
                this.slider.max = val;
                this.slider.step = (this.max - this.min) / 100;
                if (this.value > val) {
                    this.value = val;
                }
            }
        }
    }

    set unit(val) {
        this.setAttribute('unit', val);
        this.updateLabel();
    }

    set value(val) {
        if (!isNaN(val)) {
            val = parseFloat(parseFloat(val).toPrecision(4)); // Round to avoid floating point errors
            if (!(val < parseFloat(this.min) || val > parseFloat(this.max))) {
                this.setAttribute('value', val);
                this.slider.value = val;
                this.slider.style.backgroundSize = (this.value - this.min) * 100 / (this.max - this.min) + '% 100%';
                this.updateLabel();
            }
        }
    }

    updateLabel() {
        const unitLabel = this.unit ? ' ('+this.unit+')' : ''
        const str = this.textContent + unitLabel +': <b>'+this.value+'</b>';
        this.label.innerHTML = str;
    }
    

    attributeChangedCallback(name, oldValue, newValue) {
        if (newValue !== oldValue) {

            if (name === 'min') { this.min = newValue }
            if (name === 'max') { this.max = newValue }
            if (name === 'unit') { this.unit = newValue }
            if (name === 'value') { this.value = newValue }
            if (name === 'info') {this.info = newValue }

        }
        
    }

    connectedCallback() {

        // Add event listener for non-throttled changes
        this.slider.addEventListener('input', () => this.value = this.slider.value);


        // For throttled changes, dispatch event for external listeners
        this.slider.addEventListener('change', () => {
            this.dispatchEvent(new Event('change'));
        });

        this.slider.style.backgroundSize = (this.value - this.min) * 100 / (this.max - this.min) + '% 100%';

    }

    constructor() {

        super();

        this.attachShadow({mode: 'open'});

        this.shadowRoot.innerHTML = '<input-label info="placeholder"></input-label>' +
                                    '<input type="range">'

        this.label = this.shadowRoot.firstElementChild;
        this.slider = this.shadowRoot.lastElementChild;

        // Add CSS to shadow DOM
        const link = document.createElement('link');
        link.rel = 'stylesheet'; 
        link.type = 'text/css';
        link.href = 'modules/input-slider.css';
        this.shadowRoot.append(link)
    }

});