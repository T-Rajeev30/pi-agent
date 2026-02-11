const WebSocket = require("ws");
const protocol = require("./protocol");
const config = require("./config");
const events = require("./events");

let ws;

function connect() {
  ws = new WebSocket(config.RELAY);

  ws.on("open", () => {
    console.log("[INFO] Connected to relay");

    ws.send(JSON.stringify({
      type: "register",
      deviceId: config.DEVICE_ID,
      token: config.TOKEN
    }));
  });

  ws.on("message", (data) => {
    const msg = JSON.parse(data.toString());
    protocol.handleMessage(msg);
  });

  ws.on("close", () => {
    console.warn("[WARN] Relay connection closed");
    setTimeout(connect, 3000);
  });

  ws.on("error", () => {});
}

// 🔁 EVENTS → RELAY
events.on("upload_progress", (data) => {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "upload_progress", ...data }));
  }
});

events.on("recording_complete", (data) => {
  if (ws?.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "recording_complete", ...data }));
  }
});

connect();

