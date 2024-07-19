import { BaseChat } from "./chat.js";
import { Peer } from 'https://cdn.jsdelivr.net/npm/peerjs@1.5.4/+esm';
import { sysUser } from "./chat.js";
import { Message } from "./chat.js";

const errinfo =
{
    "browser-incompatible": {
        "fatal": true,
        "desc": "Your browser does not support the required WebRTC features.",
        "readabletitle": "Browser Incompatible"
    },
    "disconnected": {
        "fatal": false,
        "desc": "You've already been disconnected from the server and can no longer make any new connections.",
        "readabletitle": "Disconnected"
    },
    "invalid-id": {
        "fatal": true,
        "desc": "The PeerID contains illegal characters.",
        "readabletitle": "Invalid PeerID"
    },
    "invalid-key": {
        "fatal": true,
        "desc": "The API key in use contains illegal characters or is not in the system.",
        "readabletitle": "Invalid API Key"
    },
    "network": {
        "fatal": false,
        "desc": "Lost or cannot establish a connection to the server.",
        "readabletitle": "Network Error"
    },
    "peer-unavailable": {
        "fatal": false,
        "desc": "The peer you're trying to connect to does not exist.",
        "readabletitle": "Peer Unavailable"
    },
    "ssl-unavailable": {
        "fatal": true,
        "desc": "PeerJS is being used securely, but the cloud server does not support SSL. Yell at the developer of this chat client for help.",
        "readabletitle": "SSL Unavailable"
    },
    "server-error": {
        "fatal": true,
        "desc": "Unable to reach the server.",
        "readabletitle": "Server Error"
    },
    "socket-error": {
        "fatal": true,
        "desc": "An error from the underlying socket.",
        "readabletitle": "Socket Error"
    },
    "socket-closed": {
        "fatal": true,
        "desc": "The underlying socket closed unexpectedly.",
        "readabletitle": "Socket Closed"
    },
    "unavailable-id": {
        "fatal": true,
        "desc": "The PeerID requested is already taken.",
        "readabletitle": "PeerID Unavailable"
    },
    "webrtc": {
        "fatal": false,
        "desc": "WebRTC Error (check console for info)",
        "readabletitle": "WebRTC Error"
    },
    "no-selfconnect": {
        "fatal": false,
        "desc": "Can't connect to self.",
        "readabletitle": "Can't connect to self"
    },
    "not-connected": {
        "fatal": false,
        "desc": "You need to be connected to a peer to send messages.",
        "readabletitle": "Connection required to send messages"
    }
}



export class P2PChat extends BaseChat {
    static get connectcfg() {
        return {
            id: 'p2p',
            label: 'Connect to: ',
            placeholder: 'PeerID',
            value: '" regex="[a-zA-Z0-9]{6}' // code injection, but intended
        };
    }
    static makeid(len) {
        function dec2hex (dec) {
            return dec.toString(16).padStart(2, "0")
        }
        var arr = new Uint8Array((len || 40) / 2)
        window.crypto.getRandomValues(arr)
        return Array.from(arr, dec2hex).join('')
    }
    
    constructor(app) {
        super(app);
        this.peer = new Peer(P2PChat.makeid(6));
        this.connected = false;
        this.currentConnection = null;
        this.peer.on('connection', conn => {
            app.onMessage(new Message('Connection Failed from: ' + conn.peer, sysUser));
            if (this.currentConnection) {
                app.onMessage(new Message('Connection Failed from: ' + conn.peer, sysUser));
                conn.close();
                return;
            }
            this.connected = true;
            conn.on('data', data => {
                console.log('Received', data);
                this.onMessage(data);
            });
        });
        this.peer.on('error', err => {
            console.error(err);
            if (errinfo[err.type].fatal) {
                this.connected = false;
            }
            app.onError(errinfo[err.type].desc);
        });
        this.peer.on('open', id => {
            this.id = id;
            app.onMessage(new Message('Connected to PeerJS server as <strong>' + id + '</strong>', sysUser));
        });
    }
    connect(peerid) {
        if (this.currentConnection) {
            this.currentConnection.close();
        }
        this.currentConnection = this.peer.connect(peerid);
        this.currentConnection.on('open', () => {
            this.connected = true;
            this.app.onMessage(new Message('Connected to ' + peerid, sysUser));
        });
        this.currentConnection.on('data', data => {
            this.onMessage(data);
        });
    }
    disconnect() {
        if (this.currentConnection) {
            this.currentConnection.close();
        }
        this.connected = false
    }
    async sendMessage(message) {
        if (!this.connected) {
            this.app.onError(errinfo["not-connected"].desc, true);
            return
        }
        this.currentConnection.send(message);
        this.onMessage(message);
    }
    onMessage(message) {
        this.messages.push(message);
        this.app.onMessage(message);
    }
}

