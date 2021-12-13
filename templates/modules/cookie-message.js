window.customElements.define('cookie-message', class extends HTMLElement {

    static get observedAttributes() {
        return ['visible'];
    }

    get visible() {
        return this.getAttribute('visible');
    }

    set visible(val) {
        // Cast string values to boolean
        val = val==='true' ? true : val;
        val = val==='false' ? false : val;
        // If resultant value is a boolean, set visibility
        if (typeof val === 'boolean') {
            this.setAttribute('visible', val);
            if (val) {
                this.content.className = 'visible';
            } else {
                this.content.classList.add('closed');
            }
        }
    }

    connectedCallback() {
        // If cookie message has already been accepted, don't display
        const cookies = document.cookie.split(';');
        for (const i in cookies) {
            const cookie = cookies[i].trim().split('=');
            if (cookie[0] === 'acceptcookies' && cookie[1] === 'true'){
                this.visible = false;
            }
        }
        // Otherwise, set visible to true
        if (typeof this.visible === 'undefined' || this.visible === null) {
            this.visible = true;
        }
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (newValue !== oldValue) {
            if (name === 'visible') { this.visible = newValue; }
        }
    }


    constructor() {

        super();

        this.attachShadow({mode: 'open'});

        this.shadowRoot.innerHTML = '<div>' +
                                    '   <p>' +
                                    '       This page uses cookies to save your actions' +
                                    '       across multiple sessions. By continuing to' +
                                    '       use this site, you are consenting to our use' +
                                    '       of cookies.' +
                                    '   </p>' +
                                    '   <button type="button"><b>I understand</b></button>'
                                    '<div>'

        // Define button click behavior
        this.content = this.shadowRoot.firstElementChild;
        this.button = this.shadowRoot.querySelector('button');

        this.button.addEventListener('click', () => {
            this.visible = false;
            const exp_date = new Date( new Date().getTime() + 30 * 24 * 60 * 60 * 1000 );  // Add a month to current date
            document.cookie = 'acceptcookies=true; expires=' + exp_date.toUTCString() + '; SameSite=Strict;';
        });
        

        // Add CSS to shadow DOM
        const link = document.createElement('link');
        link.rel = 'stylesheet'; 
        link.type = 'text/css';
        link.href = 'modules/cookie-message.css';
        this.shadowRoot.append(link)
    }

});