window.customElements.define('input-label', class extends HTMLElement {


    static get observedAttributes() {
        return ['info'];
    }


    get info() {
        return this.hasAttribute('info') ? this.getAttribute('info') : '';
    }

    set info(content) {
        if (content) {
            this.setAttribute('info', content);
            this.icon.setAttribute('data-tooltip', content);
            this.icon.style.display = 'block';
        } else {
            this.icon.style.display = 'none';
        }
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (newValue !== oldValue) {
            this.info = newValue;
        }
        
    }

    constructor() {

        super();

        this.attachShadow({mode: 'open'});

        
        this.container = document.createElement('div');
        this.container.classList.add('label-container');
        this.label = document.createElement('label');
        this.label.appendChild(document.createElement('slot'));
        this.icon = document.createElement('label');
        this.icon.classList.add('info');
        this.icon.textContent = '\uD83D\uDEC8';
        this.icon.style.display = 'none';
        this.container.appendChild(this.label);
        this.container.appendChild(this.icon);
        this.shadowRoot.append(this.container);

        // Add CSS to shadow DOM
        const link = document.createElement('link');
        link.rel = 'stylesheet'; 
        link.type = 'text/css';
        link.href = 'modules/input-label.css';
        this.shadowRoot.append(link)
    }

});