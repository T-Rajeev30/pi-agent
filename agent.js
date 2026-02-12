require("dotenv").config();

const WebSocket = require("ws");
const recorder = require("./camera/recorder");

const RELAY_URL = process.env.RELAY_URL;
const DEVICE_ID = process.env.DEVICE_ID;
const DEVICE_TOKEN = process.env.DEVICE_TOKEN;

if (!RELAY_URL || !DEVICE_ID || !DEVICE_TOKEN) {
  console.error("Missing env variables");
  process.exit(1);
}

let ws = null;
let heartbeatTimer = null;

/* ---------- SAFE SEND ---------- */

function send(msg) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify(msg));
}

/* ---------- HEARTBEAT ---------- */

function startHeartbeat() {
  if (heartbeatTimer) return;

  heartbeatTimer = setInterval(() => {
    send({
      type: "heartbeat",
      deviceId: DEVICE_ID,
      recording: recorder.isRecording(),
    });
  }, 5000);
}

/* ---------- CONNECT ---------- */

function connect() {
  console.log("[PI] Connecting to relay");

  ws = new WebSocket(RELAY_URL);

  ws.on("open", () => {
    console.log("[PI] Connected");

    /* register device */
    send({
      type: "register",
      deviceId: DEVICE_ID,
      token: DEVICE_TOKEN,
    });

    startHeartbeat();
  });

  ws.on("message", async (raw) => {
    let msg;
    try {
      msg = JSON.parse(raw.toString());
    } catch {
      return;
    }

    /* ---------- START RECORDING ---------- */

    if (msg.type === "command" && msg.action === "start_recording") {
      console.log("[PI] Start recording command");

      send({
        type: "recording_started",
        deviceId: DEVICE_ID,
      });

      try {
        const url = await recorder.startRecording(
          msg.duration,
          (percent) => {
            send({
              type: "upload_progress",
              deviceId: DEVICE_ID,
              percent,
            });
          },
          msg.testSeconds || null,
        );

        send({
          type: "recording_complete",
          deviceId: DEVICE_ID,
          recordingId: msg.recordingId,
          videoUrl: url,
        });

      } catch (err) {
        console.error("Recording failed:", err.message);
      }
    }

    /* ---------- STOP RECORDING ---------- */

    if (msg.type === "command" && msg.action === "stop_recording") {
      console.log("[PI] Stop recording command");
      recorder.stopRecording();
    }
  });

  ws.on("close", () => {
    console.log("[PI] Relay disconnected → retrying");
    clearInterval(heartbeatTimer);
    heartbeatTimer = null;
    setTimeout(connect, 3000);
  });

  ws.on("error", (err) => {
    console.error("[PI] WS Error:", err.message);
  });
}

connect();
