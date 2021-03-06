// Copyright (c) 2022, W. M. Keck Observatory
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.


window.customElements.define('input-spin', class extends HTMLElement {


    static get observedAttributes() {
        return ['min', 'max', 'value', 'step', 'info'];
    }

    get info() { return this.getAttribute('info'); }
    get min() { return this.getAttribute('min'); }
    get max() { return this.getAttribute('max'); }
    get value() { return this.input.value; }
    get step() { return this.getAttribute('step'); }

    set info(val) {
        this.setAttribute('info', val);
        this.label.info = val;
    }

    set min(val) {
        if (!isNaN(val)) {
            val = parseFloat(val);
            this.setAttribute('min', val);
            if (this.max && val > this.max) {
                this.max = val;
            }
            if (this.value < val) {
                this.value = val;
            }
            if (isNaN(val)) {
                this.setAttribute('min', null);
            }
        }
    }

    set max(val) {
        if (!isNaN(val)) {
            val = parseFloat(val);
            this.setAttribute('max', parseFloat(val));
            if (this.min && val < this.min) {
                this.min = val;
            }
            if (this.value > val) {
                this.value = val;
            }
            if (isNaN(val)) {
                this.setAttribute('max', null);
            }
        }
    }

    set step(val) {
        if (!isNaN(val)) {
            this.setAttribute('step', parseFloat(val));
        }
    }

    set value(val) {
        // Round to 6 sig-figs to avoid floating point errors
        this.input.value = parseFloat(parseFloat(val).toPrecision(6));
        // Dispatch event to trigger proper change callback
        this.input.dispatchEvent(new Event('change'));
    }
    

    attributeChangedCallback(name, oldValue, newValue) {
        if (newValue !== oldValue) {

            if (name === 'min') { this.min = newValue }
            if (name === 'max') { this.max = newValue }
            if (name === 'step') { this.step = newValue }
            if (name === 'value') { this.value = newValue }
            if (name === 'info') {this.info = newValue }

        }
        
    }

    connectedCallback() {
        // Define default values
        if (!this.step) {
            this.step = 1;
        }
        if (!this.value) {
            this.value = 0;
        }
        this.setAttribute('oldValue', this.value);
    }

    constructor() {

        super();

        this.attachShadow({mode: 'open'});

        this.shadowRoot.innerHTML = '<input-label><slot></slot>:</input-label>' +
                                    '<div>' +
                                    '   <input type="text" value=0>' +
                                    '   <button class="up"></button>' +
                                    '   <button class="down"></button>' +
                                    '</div>'

        this.label = this.shadowRoot.firstElementChild;
        this.input = this.shadowRoot.lastElementChild.children[0];
        this.upButton = this.shadowRoot.lastElementChild.children[1];
        this.downButton = this.shadowRoot.lastElementChild.children[2];

        this.upButton.addEventListener('click', () => this.stepValue(1));
        this.downButton.addEventListener('click', () => this.stepValue(-1));

        // Update value when user types changes into input element
        this.input.addEventListener('change', () => {
            const val = parseFloat(this.input.value);
            if (!isNaN(val)) {
                this.input.value = val;

                if (val < parseFloat(this.min)) this.input.value = this.min;

                if (val > parseFloat(this.max)) this.input.value = this.max;

                this.dispatchEvent(new Event('change'));

                this.setAttribute('oldValue', this.input.value);
            } else {
                this.input.value = this.getAttribute('oldValue');
            }
        });

        // Add CSS to shadow DOM
        const link = document.createElement('link');
        link.rel = 'stylesheet'; 
        link.type = 'text/css';
        link.href = 'src/modules/input-spin.css';
        this.shadowRoot.append(link)
    }


    stepValue(direction) {
        // Default to a step size of 1 if not specified
        const step = !isNaN(this.step) ? this.step : 1;
        // Increment/decrement value by step size, rounded to 6 sig-figs to avoid floating point errors
        const val = parseFloat(this.value) + direction * step;
        if (!(val < parseFloat(this.min) || val > parseFloat(this.max))) {
            this.value = val;
        }
    }


});
