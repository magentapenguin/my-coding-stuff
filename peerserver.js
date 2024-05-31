const { PeerServer } = require("peer");
const Ncrypto = require("crypto");

const peerServer = PeerServer({ 
    port: 8081, 
    path: "/",
    proxied: true,
    generateClientId: () => {
        return Ncrypto.randomBytes(8).toString("hex");
    },
    corsOptions: {
        origin: "http://bookish-system-jgvv7pxj96wh5wjq-8080.app.github.dev/",
        methods: ["GET", "POST"]
    }
});