// WebSocket connection logic
const WebSocket = require("ws");
const config = require("./config");
const protocol = require("./protocol");
const logger = require("./logger");

let ws;

function connect(onShellOutput) {
  logger.info("Connecting to relay...");

  ws = new WebSocket(config.RELAY);

  ws.on("open", () => {
    logger.info("Connected to relay");

    ws.send(JSON.stringify({
      type: "register",
      deviceId: config.DEVICE_ID,
      token: config.TOKEN,
    }));
  });

  ws.on("message", (raw) => {
    let msg;
    try {
      msg = JSON.parse(raw.toString());
    } catch {
      return;
    }

    protocol.handleMessage(msg);
  });

  ws.on("close", () => {
    logger.error("Disconnected. Reconnecting...");
    setTimeout(() => connect(onShellOutput), 3000);
  });

  ws.on("error", () => {});

  // expose send method
  return {
    send: (data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
      }
    },
  };
}

module.exports = { connect };
