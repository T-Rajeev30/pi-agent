/**
 * agent.js
 *
 * This is the main runtime process of the Raspberry Pi device.
 * It connects to your relay server and waits for commands.
 */


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

/* ---------------- CONNECT TO RELAY ---------------- */

console.log("Connecting to relay:", RELAY_URL);
const ws = new WebSocket(RELAY_URL);

/**
 * When socket opens → register device
 */
ws.on("open", () => {
  console.log("Connected to relay");

  ws.send(JSON.stringify({
    type: "register",
    deviceId: DEVICE_ID,
    token: DEVICE_TOKEN
  }));

  startHeartbeat();
});
/**
 * Receive commands from backend
 */
ws.on("message", async raw => {
  const msg = JSON.parse(raw.toString());

  if (msg.type !== "command") return;

  /* ---------- START RECORDING ---------- */
  if (msg.action === "START" || msg.action === "start_recording" ) {
    console.log("START command received");

    ws.send(JSON.stringify({
      type: "recording_started",
      deviceId: DEVICE_ID
    }));

    try {
      const url = await recorder.startRecording();

      ws.send(JSON.stringify({
        type: "recording_complete",
        deviceId: DEVICE_ID,
        recordingId: msg.recordingId,
        videoUrl: url
      }));

    } catch (err) {
      console.error("Recording failed:", err);
    }
  }

  /* ---------- STOP RECORDING ---------- */
  if (msg.action === "stop_recording" || msg.action === "STOP") {
    console.log("STOP command received");
    recorder.stopRecording();
  }
});

/* ---------------- HEARTBEAT ---------------- */
/**
 * Sent every 5 seconds so backend knows device status.
 */
function startHeartbeat() {
  setInterval(() => {
    ws.send(JSON.stringify({
      type: "heartbeat",
      deviceId: DEVICE_ID,
      recording: recorder.isRecording()
    }));
  }, 5000);
}
