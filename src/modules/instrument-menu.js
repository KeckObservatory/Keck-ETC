// Copyright (c) 2022, W. M. Keck Observatory
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.


window.customElements.define('instrument-menu', class extends HTMLElement {

    static get observedAttributes() {
        return ['value'];
    }

    get value() { return this.getAttribute('value'); }
    

    set value(val) {

        val = val.toLowerCase();

        const instruments = [...this.querySelectorAll('option')];
        const options = instruments.map( opt => opt.id );

        if (options.includes(val) && val != this.value) {

            instruments.forEach( instr => instr.classList.remove('selected') );
            this.querySelector('#'+val).classList.add('selected');
            this.setAttribute('value', val);
            this.dispatchEvent(new Event('change'));

        } else if (!options.includes(val)) {

            throw 'Instrument ' + val + ' is not a valid option';

        }

    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (newValue !== oldValue) {
            if (name === 'value') { this.value = newValue; }
        }
    }


    constructor() {

        super();

        this.attachShadow({mode: 'open'});

        this.shadowRoot.innerHTML = '<div id="mobile-toggle">' +
                                    '   <span></span>' +
                                    '   <span></span>' +
                                    '   <span></span>' +
                                    '</div>' +
                                    '<div id="menu">' +
                                    '   <slot></slot>' +
                                    '</div>' +
                                    '<div id="background"></div>';

        this.shadowRoot.addEventListener( 'slotchange', () => {     
            const instruments = [...this.querySelectorAll('option')];
            instruments.forEach( instr => {
                // Set instrument ID to instrument name
                instr.id = instr.innerText.toLowerCase();

                // On click, go to link or set active instrument
                instr.addEventListener('click', () => {
                    if (instr.dataset.href) {
                        window.open(instr.dataset.href, '_blank');
                    } else {
                        this.value = instr.id;
                    }
                });
            });
        });

        this.toggle = this.shadowRoot.querySelector('#mobile-toggle');
        this.background = this.shadowRoot.querySelector('#background');
        const toggle = () => {
            if ([...this.toggle.classList].includes('active')) {
                this.toggle.classList.remove('active');
            } else {
                this.toggle.classList.add('active');
            }
        }

        this.toggle.addEventListener('click', toggle);
        this.background.addEventListener('click', toggle);

        // Add CSS to shadow DOM
        const link = document.createElement('link');
        link.rel = 'stylesheet'; 
        link.type = 'text/css';
        link.href = 'src/modules/instrument-menu.css';
        this.shadowRoot.append(link);
    }

});
