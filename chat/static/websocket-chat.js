import { BaseChat } from "./chat.js";
import { Message } from "./chat.js";
import { PingMessage } from "./chat.js";
import { User } from "./chat.js";

export class WebSocketChat extends BaseChat {
    static get connectcfg() {
        return {
            id: 'websocket',
            label: 'WebSocket: ',
            placeholder: 'WebSocket URL',
            value: `ws${location.protocol.match('https') ? 's':''}://${location.host}${location.pathname}/socket`
        };
    }
    constructor(app) {
        super(app);
        this.pinged = false;
    }

    ping() {
        this.sendMessage(new PingMessage());
        // wait for pong, if not received, disconnect
        setTimeout(() => {
            if (this.pinged) {
                this.pinged = false;
                return;
            }
            this.app.onError('Server Timeout');
            this.disconnect();
        }, 5000);
        
    }
    connect(url) {
        if (this.socket) {
            this.socket.close();
        }
        this.socket = new WebSocket(url);
        this.socket.onmessage = event => {
            console.log('Received', event.data);
            let message;
            try {
                message = JSON.parse(event.data);
            } catch (e) {
                message = { text: event.data, user: User.unknown };
            }
            console.log('Parsed', message);
            this.onMessage(message);
        };
        this.socket.onopen = () => {
            this.app.onMessage(new Message('Connected to ' + url, User.system));
        };
        this.socket.onerror = err => {
            this.app.onError(err);
        };
        this.pingdata = setInterval(() => {
            this.ping();
        }, 60000);
    }

    disconnect() {
        this.pingdata = clearInterval(this.pingdata);
        this.socket.close();
    }

    async sendMessage(message) {
        this.socket.send(JSON.stringify(message));
    }

    onMessage(message) {
        if (message.type === 'pong') {
            this.pinged = true;
            return;
        }
        this.messages.push(new Message(message.text, User.fromJSON(message.user), message.reply));
        this.app.onMessage(message);
    }
}