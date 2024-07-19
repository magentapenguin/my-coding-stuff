import { User } from './chat.js';

class UserElement extends HTMLElement {
    constructor() {
        super();

        
        let img = document.createElement('img');
        this.appendChild(img);

        let p = document.createElement('p');
        this.appendChild(p);
    }
    connectedCallback() {
        User.getCurrentUser().then(user => {
            console.log(user);
            if (user === undefined) {
                this.querySelector('p').textContent = 'Sign in';
                this.querySelector('img').src = '/static/img/avatar.svg';
                this.onclick = () => {
                    location.assign('/login');
                }
                return;
            }
            this.querySelector('p').textContent = user.name;
            this.querySelector('img').src = user.photoURL;
        });
        this.setAttribute('tabindex', '0');
        this.addEventListener('click', this.onclick);
        this.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                this.onclick();
            }
        });
    }
    onclick() {
        console.log('click');
        this.classList.add('loading');
        this.inert = true;
        let loader = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="icon spin"><!--!Font Awesome Pro 6.6.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2024 Fonticons, Inc.--><path d="M224 32c0-17.7 14.3-32 32-32C397.4 0 512 114.6 512 256c0 46.6-12.5 90.4-34.3 128c-8.8 15.3-28.4 20.5-43.7 11.7s-20.5-28.4-11.7-43.7c16.3-28.2 25.7-61 25.7-96c0-106-86-192-192-192c-17.7 0-32-14.3-32-32z"/></svg>`
        let loaderDiv = document.createElement('div');
        loaderDiv.innerHTML = loader;
        this.appendChild(loaderDiv);
        location.assign('/user');
    }
}

customElements.define('user-cfg', UserElement);

// Auto load avatar
document.addEventListener('DOMContentLoaded', () => {
    User.getCurrentUser().then(user => {
        document.querySelectorAll('img.avatar').forEach(img => {
            img.src = user.photoURL;
        });
    })
});