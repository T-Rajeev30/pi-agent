const WebSocket = require("ws");
const config = require("./config");
const logger = require("./logger");
const events = require("./events");

let ws;

function connect() {
  ws = new WebSocket(config.RELAY);

  ws.on("open", () => {
    logger.info("Connected to relay");

    ws.send(JSON.stringify({
      type: "register",
      deviceId: config.DEVICE_ID,
      token: config.TOKEN
    }));
  });

  ws.on("message", (data) => {
    const msg = JSON.parse(data.toString());
    if (msg.type === "command") {
      events.emit(msg.action, msg.payload);
    }
  });

  ws.on("close", () => {
    logger.warn("Relay closed. Reconnecting...");
    setTimeout(connect, 3000);
  });
}

function send(data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

module.exports = { connect, send };

