class CircleButton extends HTMLElement {
    static observedAttributes = ["content", 'borderspin'];

    constructor() {
        super();
        this.attachShadow({ mode: 'open' });

        const buttonStyle = document.createElement('style');
        buttonStyle.textContent = `
            :host {
                display: flex;
                position: relative;
                border-radius: 50%;
                width: 20vh;
                height: 20vh;
                border: transparent solid;
                background: var(--bg, #000);
                background-clip: padding-box;
                cursor: pointer;
                text-align: center;
                user-select: none;
                -webkit-user-select: none;
                /*transition: background 0.5s;*/
            }
            :host(:hover) {
                background: linear-gradient(to bottom, color-mix(in lch shorter hue, var(--bg, #000) 70%, #00e4ff), color-mix(in lch shorter hue, var(--bg, #000) 90%, #00ffaa));
                background-clip: padding-box;
            }
            .border-element {
                background: linear-gradient(to bottom, #2de5d1, #1fa4e9);
                border-radius: 50%;
                position: absolute;
                inset: -0.25rem;
                z-index: -1;
                /*animation: linear 2s spin 0s infinite;*/
            }
            .content {
                margin: auto;
                font-size: 5vh;
            }
            @keyframes spin {
                0% {
                    transform: rotate(0deg);
                }
                100% {
                    transform: rotate(360deg);
                }
            }
        `;
        this.shadowRoot.appendChild(buttonStyle);

        const pseudoElement = document.createElement('div');
        pseudoElement.classList.add('border-element');
        this.shadowRoot.appendChild(pseudoElement);

        const textElement = document.createElement('span');
        textElement.classList.add('content');
        this.shadowRoot.appendChild(textElement);
        
    }
    attributeChangedCallback(name, oldValue, newValue) {
        if (name == 'content') {
            this.shadowRoot.querySelector('.content').textContent = newValue
        } else if (name == 'borderspin') {
            this.shadowRoot.querySelector('.border-element').style.transform = 'rotate('+newValue+'deg)'
        }
    }
}
customElements.define('circle-button', CircleButton);