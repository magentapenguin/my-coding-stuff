
class NavMenu extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({mode: 'open'});
        this.burger = document.createElement('svg');
        this.burger.setAttribute('viewBox', '0 0 24 24');
        this.burger.setAttribute('fill', 'none');
        this.burger.setAttribute('stroke', 'currentColor');
        this.burger.setAttribute('stroke-width', '2');
        this.burger.setAttribute('stroke-linecap', 'round');
        this.burger.setAttribute('stroke-linejoin', 'round');
        this.burger.innerHTML = '<path d="M3 12h18M3 6h18M3 18h18"></path>';
        this.burger.style.display = 'block';
        this.burger.style.width = '24px';
        this.burger.style.height = '24px';
        this.burger.style.cursor = 'pointer';
        this.burger.style.color = 'white';
        this.burger.style.position = 'absolute';
        this.burger.style.top = '10px';
        this.burger.style.left = '10px';
        this.burger.addEventListener('click', () => {
            this.dispatchEvent(new CustomEvent('toggle'));
        });
        this.shadowRoot.appendChild(this.burger);
    }
}

customElements.define('nav-menu', NavMenu);