const recorder = require("./camera/recorder");
const events = require("./events");
const config = require("./config");
const { sendToRelay } = require("./connection/relay");

let activeScheduleId = null;

async function handleMessage(msg) {
  if (!msg || msg.type !== "command") return;

  /* ================= START ================= */

  if (msg.action === "start_recording") {
    activeScheduleId = msg.payload.scheduleId;

    recorder.startRecording({
      scheduleId: activeScheduleId
    });

    return;
  }

  /* ================= STOP ================= */

  if (msg.action === "stop_recording") {
    if (!activeScheduleId) {
      console.error("No active scheduleId");
      return;
    }

    const videoUrl = await recorder.stopRecording();

    sendToRelay({
      type: "recording_complete",
      deviceId: config.DEVICE_ID,
      scheduleId: activeScheduleId,
      videoUrl
    });

    activeScheduleId = null;
  }
}

module.exports = { handleMessage };

