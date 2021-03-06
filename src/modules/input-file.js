// Copyright (c) 2022, W. M. Keck Observatory
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.


window.customElements.define('input-file', class extends HTMLElement {

    static get observedAttributes() {
        return ['info', 'file', 'accept'];
    }

    get info() { return this.getAttribute('info'); }

    get file() { return this.getAttribute('file'); }

    get accept() { return this.getAttribute('accept'); }

    set info(val) {
        this.setAttribute('info', val);
        this.label.info = val;
    }

    set accept(val) {
        this.setAttribute('accept', val);
        this.input.accept = val;
    }

    set file(val) {
        // If new value is a file object, parse appropriately
        if (typeof val === 'object' && val instanceof File ) {
            // Check file type against allowed file types
            if ( this.accept && this.accept.split(',').filter(type => val.name.endsWith(type)).length == 0 ) {
                return;
            }
            const reader = new FileReader();
            reader.onload = () => {
                this.setAttribute('file', val.name.replace(/\s+/g, '') + ',' + reader.result.split(',').at(-1) );
                this.icon.src = 'src/static/post-file-upload.svg';
                this.dispatchEvent(new Event('change'));
            }
            reader.readAsDataURL(val);
        } else if (typeof val === 'string') {
            this.setAttribute('file', val);
            this.icon.src = 'src/static/post-file-upload.svg';
            this.dispatchEvent(new Event('change'));
        } else {
            this.icon.src = 'src/static/pre-file-upload.svg';
        }
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (newValue !== oldValue) {
            if (name === 'info') { this.info = newValue; }
            if (name === 'file') { this.file = newValue; }
            if (name === 'accept') { this.accept = newValue; }
        }
    }


    constructor() {

        super();

        this.attachShadow({mode: 'open'});

        this.shadowRoot.innerHTML = '<input-label><slot></slot>:</input-label>' +
                                    '<div class="dropbox"><img src="src/static/pre-file-upload.svg"></img></div>' +
                                    '<input type="file">';
        
        this.label = this.shadowRoot.firstElementChild;
        this.input = this.shadowRoot.lastElementChild;
        this.dropbox = this.shadowRoot.querySelector('.dropbox');
        this.icon = this.shadowRoot.querySelector('img');

        // Add functionality to dropbox via event listeners
        this.dropbox.addEventListener('click', () => this.input.click());
        this.dropbox.addEventListener("dragover", e => { 
            e.stopPropagation();
            e.preventDefault();
            // TODO -- check against allowed file types and display appropriate dropEffect
            e.dataTransfer.dropEffect = 'copy';
            this.dropbox.classList.add('hover');
        }, false);
        this.dropbox.addEventListener("dragenter", e => {
            e.stopPropagation();
            e.preventDefault();
            this.dropbox.classList.add('hover');
        }, false);
        this.dropbox.addEventListener("dragleave", e => {
            e.stopPropagation();
            e.preventDefault();
            this.dropbox.classList.remove('hover');
        }, false);
        this.dropbox.addEventListener("drop", e => {
            e.stopPropagation();
            e.preventDefault();
            this.file = e.dataTransfer.files[0];
            // Animate click effect
            this.dropbox.classList.add('active');
            setTimeout( () => {
                this.dropbox.classList.remove('active');
                this.dropbox.classList.remove('hover');
            }, 100);
        }, false);
        // Add functionalaity to file input via event listeners
        this.input.addEventListener('change', () => {
            this.file = this.input.files[0];
        });

        // Add CSS to shadow DOM
        const link = document.createElement('link');
        link.rel = 'stylesheet'; 
        link.type = 'text/css';
        link.href = 'src/modules/input-file.css';
        this.shadowRoot.append(link)
        
    }

});
