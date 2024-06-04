import {
    computePosition,
    flip,
    size,
    autoUpdate,
} from 'https://cdn.jsdelivr.net/npm/@floating-ui/dom@1.6.3/+esm';

export class Dropdown {
    constructor(dropdown) {

        this.dropdown = dropdown;
        this.button = this.dropdown.querySelector('[data-dropdown]');
        this.menu = this.dropdown.querySelector('.dropdown-contents');

        this.button.addEventListener('mouseenter', this.onOpen.bind(this));
        this.button.addEventListener('mouseleave', this.onClose.bind(this));

        console.log('Dropdown initialized', this.dropdown, this.button, this.menu);

        this.cleanup = () => {};
    }
    onOpen() {
        this.dropdown.setAttribute('data-open', 'true');
        this.cleanup = autoUpdate(this.button, this.menu, () => {
            computePosition(this.button, this.menu, {
                middleware: [
                    flip({padding: 5}),
                    size({
                        padding: 5,
                        apply({availableWidth, availableHeight, elements}) {
                            // Change styles, e.g.
                            Object.assign(elements.floating.style, {
                                maxWidth: `${availableWidth}px`,
                                maxHeight: `${availableHeight}px`,
                            });
                        },
                    }),
                    
                ],
                placement: this.button.getAttribute('data-dropdown-placement') ?? 'bottom-start',
            }).then(({x, y}) => {
                Object.assign(this.menu.style, {
                    left: `${x}px`,
                    top: `${y}px`,
                });
            });
        });
    }
    onClose() {
        this.dropdown.setAttribute('data-open', 'false');
        this.cleanup();
    }
}

export function initDropdowns() {
    document.querySelectorAll('.dropdown').forEach(dropdown => new Dropdown(dropdown));
}