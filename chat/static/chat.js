import dompurify from 'https://cdn.jsdelivr.net/npm/dompurify/+esm';
import markdownIt from "https://cdn.jsdelivr.net/npm/markdown-it@14.1.0/+esm";
/*
import markdownItAttrs from 'https://cdn.jsdelivr.net/npm/markdown-it-attrs@4.1.6/+esm'
import markdownItAnchor from 'https://cdn.jsdelivr.net/npm/markdown-it-anchor@9.0.1/+esm';
*/
import markdownItAbbr from 'https://cdn.jsdelivr.net/npm/markdown-it-abbr@2.0.0/+esm';
import markdownItDeflist from 'https://cdn.jsdelivr.net/npm/markdown-it-deflist@3.0.0/+esm';


const md = markdownIt({
    html: false,
    linkify: true,
    typographer: true
});
/*
md.use(markdownItAttrs);
md.use(markdownItAnchor, {
    level: 1,
    permalink: true,
    permalinkBefore: true,
    permalinkSymbol: "#",
});
*/
md.use(markdownItAbbr);
md.use(markdownItDeflist);



async function sha256(string) {
    const buffer = new TextEncoder('utf-8').encode(string);
    const hash = await crypto.subtle.digest('SHA-256', buffer);
    return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
}

function fixinput(element) {
    if (element instanceof HTMLElement) {
        return element;
    }
    return document.querySelector(element);
}

export async function renderMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');
    if (message?.classList !== undefined) {
        messageElement.classList.add(message.classList)
    }
    messageElement.innerHTML = dompurify.sanitize(`
        <div class="header">
            <img src="${message?.user?.photoURL ?? User.unknown.photoURL}">
            <div class="username"></div>
        </div>
        <div class="main">
            ${message?.reply ? `<div class="reply"></div>` : ''}
            <div class="text">${dompurify.sanitize(md.render(message.text))}</div>
            <div class="date">${new Date(message?.createdAt).toLocaleString()}</div>
        </div>
    `, { USE_PROFILES: { html: true }, FORBID_TAGS: ['style','link']});
    messageElement.querySelector('.username').textContent = message?.user?.name ?? User.unknown.name;
    return messageElement;
}

// An alias for User.getCurrentUser()
export async function getUser() {
    return User.getCurrentUser();
}

// Connect UI for the chat
export function connectui(done,info,where,exit) {
    const form = document.createElement('form');
    form.classList.add('connect-form');
    form.innerHTML = `
        <label for="${info.id}">${info.label}</label>
        <input type="text" id="${info.id}" placeholder="${info.placeholder}" ${info.value ? `value="${info.value}"` : ''} autofill="off">
        <button type="submit">Connect</button>
        <button class="disconnect" disabled>Disconnect</button>
    `;

    form.addEventListener('submit', event => {
        event.preventDefault();
        done(document.getElementById(info.id).value);
    });
    form.querySelector('.disconnect').addEventListener('click', event=>{
        event.preventDefault();
        exit();
    });
    if (where) {
        fixinput(where).appendChild(form);
    }
    return form;
}

// Very Hacky
function addMessage2DOM(message, where) {
    (async () => {
        fixinput(where).appendChild(await renderMessage(message));
    })();
}

export function setupChat(messages, where) {
    const form = document.createElement('form');
    form.classList.add('chat-form');
    form.innerHTML = `
        <input type="text" name="message" placeholder="Type a message..." autofill="off">
        <button type="submit">Send</button>
    `;

    // Render messages
    const messagesElement = document.createElement('div');
    messagesElement.id = 'messages';

    messages.forEach(message => {
        addMessage2DOM(message, messagesElement);
    });
    if (where) {
        fixinput(where).appendChild(messagesElement);
        fixinput(where).appendChild(form);
    }
    return [messagesElement, form];
}

export class BaseChat {
    constructor(app) {
        this.app = app;
        this.app.chat = this;
        this.messages = [];
    }

    async sendMessage(message) {
        throw new Error('Not implemented');
    }
    onMessage(message) {
        throw new Error('Not implemented');
    }
    connect() {
        throw new Error('Not implemented');
    }
}

export class Message {
    constructor(text, user, classList, reply, createdAt) {
        this.text = text;
        this.user = user ?? User.unknown;
        this.reply = reply;
        this.createdAt = createdAt ?? new Date();
        this.classList = classList;
        this.type = 'message';
    }
    static fromJSON(json) {
        return new Message(json.text, User.fromJSON(json.user), json.classList, json.reply, new Date(json.createdAt));
    }
    async hash() {
        return await sha256(this.text + this.user.email + this.createdAt);
    }
}

export class PingMessage extends Message {
    constructor() {
        super('Ping', User.system);
        this.type = 'ping';
    }
}

export class User {
    constructor(name, email, photoURL, id) {
        this.name = name;
        if (!photoURL) {
            (async () => {
                let hash = await sha256(email);
                this.photoURL = 'https://www.gravatar.com/avatar/' + hash + '?d=mp';
            }).bind(this)();
        } else {
            this.photoURL = photoURL;
        }
        this.id = id;

    }

    static async makeAsync(name, email, photoURL, id) {
        let out = User.unknown;
        out.name = name;
        if (!photoURL) {
            let hash = await sha256(email);
            out.photoURL = 'https://www.gravatar.com/avatar/' + hash + '?d=mp';
        } else {
            out.photoURL = photoURL;
        }
        out.id = id;
        return out;
    }

    static async getCurrentUser() {
        try {
            var out = await fetch('/api/user')
            console.log(out)
            out = await out.json()
            console.log(out)
        } catch (e) {
            console.error(e);
            return undefined;
        }
        out = await User.fromJSONAsync(out)
        cachedUser = out
        return out
    }
    static getcachedCurrentUser() {
        return cachedUser;
    }
    static fromJSON(json) {
        if (typeof json !== 'object') {
            try {
                json = JSON.parse(json);
            } catch {
                console.error('Invalid JSON', json);
                return undefined;
            }
        }
        return new User(json.name, json.email, json.photoURL, json.id);
    }
    static async fromJSONAsync(json) {
        if (typeof json !== 'object') {
            try {
                json = JSON.parse(json);
            } catch {
                console.error('Invalid JSON', json);
                return undefined;
            }
        }
        return await User.makeAsync(json.name, json.email, json.photoURL, json.id);
    }
    static get system() {
        return new User('System', 'N/A', 'https://www.gravatar.com/avatar/000000000000000000000000000000000000000000000000000000?d=mp');
    }
    static get unknown() {
        return new User('Anonymous', 'N/A', '/static/img/avatar.svg');
    }
    static get self() {
        return new User('You', 'N/A', cachedUser.photoURL ?? '/static/img/avatar.svg');
    }
}

var cachedUser = User.unknown;
User.getCurrentUser(); // Preload user


export class App {
    get messages() {
        return this.chat.messages;
    }
    set messages(value) {
        this.chat.messages = value;
    }
    constructor(chatClass) {
        this.chatClass = chatClass;
        this.chat = null;
        this.dom = {
            messages: null,
            form: null,
            prestart: null,
        };
        this.where = document.querySelector('#chat');
    }
    init() {
        this.chat = new this.chatClass(this);
        this.dom.prestart = connectui(this.connect.bind(this), this.chatClass.connectcfg, this.where, this.disconnect.bind(this));
        this.start();
    }
    start() {
        let dom = setupChat(this.messages, this.where);
        this.dom.messages = dom[0];
        this.dom.form = dom[1];
        this.dom.form.addEventListener('submit', this.onSubmit.bind(this));
        console.log(this.dom);
    }
    connect(data) {
        this.dom.prestart.querySelector('button').disabled = true;
        this.chat.connect(data);
        this.dom.prestart.querySelector('button.disconnect').disabled = false;
    }
    disconnect() {
        this.dom.prestart.querySelector('button').disabled = false;
        this.dom.messages.innerHTML = '';
        this.chat.disconnect();
        this.dom.prestart.querySelector('button.disconnect').disabled = true;
    }
    rerender() {
        this.dom.messages.innerHTML = '';
        this.messages.forEach(message => {
            addMessage2DOM(message, this.dom.messages);
        });
    }
    onSubmit(event) {
        event.preventDefault();
        (async ()=>{
        const message = new Message(this.dom.form.querySelector('input[name="message"]').value, User.self);
        await User.getCurrentUser() // Update cached user
        this.sendMessage(message)
            .then(() => {
                this.dom.form.querySelector('input[name="message"]').value = '';
            });
        })();
    }
    onMessage(message) {
        if (message.user === undefined) {
            message.user = User.unknown;
        }
        if (message.user.name === User.self.name) {
            message.user = User.getcachedCurrentUser() ?? User.unknown;
        }
        console.log('Received', message);
        addMessage2DOM(message, this.dom.messages);
    }
    async sendMessage(message) {
        if (message.user === undefined) {
            message.user = User.unknown;
        }
        if (message.user.name === User.self.name) {
            message.user = User.getcachedCurrentUser() ?? User.unknown;
        }
        console.log('Sending', message);
        await this.chat.sendMessage(message);
    }
    onError(error, delprevmessage = false) {
        try {
            this.dom.prestart.querySelector('button').disabled = false;
        } catch {}
        try {
            this.dom.prestart.querySelector('button.disconnect').disabled = true;
        } catch {}
        console.error(error);
        try {
            addMessage2DOM(new Message(error, sysUser, "error"), this.dom.messages)
        } catch {}
        if (delprevmessage) {
            this.messages.pop();
        }
    }
}