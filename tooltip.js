import {
    computePosition,
    flip,
    shift,
    offset,
    arrow,
    autoUpdate,
} from 'https://cdn.jsdelivr.net/npm/@floating-ui/dom@1.6.3/+esm';

export class Tooltip {
    constructor(button) {
        this.tooltip = document.createElement('div');
        this.tooltip.classList.add('tooltip');
        
        this.arrowEl = document.createElement('div');
        this.arrowEl.classList.add('tooltip__arrow');

        this.button = button;
        this.button.addEventListener('mouseenter', this.onHover.bind(this));
        this.button.addEventListener('mouseleave', this.onHoverEnd.bind(this));
        
        if (this.button.title) {
            this.button.setAttribute('data-tooltip-text', this.button.title);
            this.button.title = '';
        }

        this.cleanup = () => {};
    }
    onHover() {
        this.tooltip.innerText = this.button.getAttribute('data-tooltip-text');
        this.tooltip.appendChild(this.arrowEl);
        document.body.appendChild(this.tooltip);
        if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.tooltip.animate([{opacity: 0}, {opacity: 1}], {duration: 200, fill: 'forwards'});
        }
        this.cleanup = autoUpdate(this.button, this.tooltip, () => {
            computePosition(this.button, this.tooltip, {
                middleware: [offset(8), flip(), shift({padding: 5}), arrow({element: this.arrowEl})],
                placement: this.button.getAttribute('data-tooltip-placement') ?? 'top',
            }).then(({x, y, placement, middlewareData}) => {
                Object.assign(this.tooltip.style, {
                    left: `${x}px`,
                    top: `${y}px`,
                });
                const {x: arrowX, y: arrowY} = middlewareData.arrow;

                const staticSide = {
                    top: 'bottom',
                    right: 'left',
                    bottom: 'top',
                    left: 'right',
                }[placement.split('-')[0]];
                
                console.log(placement, staticSide);

                let top = (arrowY ?? 0) + (staticSide === 'top' ? -5 : 0);
                let left = (arrowX ?? 0) + (staticSide === 'left' ? -5 : 0);
                let right = staticSide === 'right' ? -5 : 0;
                let bottom = staticSide === 'bottom' ? 0 : 0;

                console.log(top, left, right, bottom);

                let style = {
                    left: left !== 0 ? (left+'px') : '' ,
                    top: top !== 0 ? (top+'px') : '',
                    right: right !== 0 ? (right+'px') : '',
                    bottom: bottom !== 0 ? (bottom+'px') : '',
                }

                console.log(style);

                Object.assign(this.arrowEl.style, style);
            });
        });
    }
    onHoverEnd() {
        if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            this.tooltip.animate([{opacity: 1}, {opacity: 0}], {duration: 100, fill: 'forwards'}).onfinish = () => {
                this.tooltip.remove();
                this.cleanup();
            };
        } else {
            this.tooltip.remove();
            this.cleanup();
        }
    }
}

export function initTooltips() {
    document.querySelectorAll('[data-tooltip="true"]').forEach((button) => {
        new Tooltip(button);
    });
}