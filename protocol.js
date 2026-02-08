const recorder = require("./media/recorder");

let activeScheduleId = null;

async function handleMessage(msg) {
  // START RECORDING
  if (msg.type === "command" && msg.action === "start_recording") {
    activeScheduleId = msg.payload.scheduleId;

    recorder.startRecording({
      arenaId: msg.payload.arenaId,
      startTime: msg.payload.startTime,
      endTime: "auto",
      profile: msg.payload.profile,
    });
    return;
  }

  // STOP RECORDING
  if (msg.type === "command" && msg.action === "stop_recording") {
    if (!activeScheduleId) {
      console.error("No active scheduleId — cannot complete recording");
      return;
    }

    const videoUrl = await recorder.stopRecording();

    global.__ws__.send({
      type: "recording_complete",
      deviceId: global.__deviceId__,
      scheduleId: activeScheduleId,
      fileUrl: videoUrl,
    });

    activeScheduleId = null;
    return;
  }
}

module.exports = { handleMessage };

