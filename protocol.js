const recorder = require("./media/recorder");

exports.handleMessage = (msg) => {
  if (!msg || msg.type !== "command") return;

  if (msg.action === "start_recording") {
    recorder.startRecording(msg.payload);
  }

  if (msg.action === "stop_recording") {
    recorder.stopRecording();
  }
};

