
const { spawn } = require("child_process");
const convert = require("./converter");
const upload = require("./uploader");
const events = require("../events");

let proc = null;
let activeScheduleId = null;

exports.startRecording = ({ scheduleId }) => {
  if (proc) return console.log("Recording already running");
  if (!scheduleId) return console.error("Missing scheduleId");

  activeScheduleId = scheduleId;

  console.log("🎥 START RECORDING", scheduleId);

  proc = spawn("rpicam-vid", [
  "--inline",
  "--timeout", "0",
  "--width", "1280",
  "--height", "720",
  "--framerate", "60",
  "--bitrate", "8000000",   // 🔥 8 Mbps (important)
  "-o", `${scheduleId}.h264`
]);


  proc.on("exit", () => proc = null);
};

exports.stopRecording = async () => {
  if (!proc) return console.log("No active recording");

  console.log("🛑 STOP RECORDING");
  proc.kill("SIGINT");
  proc = null;

  const inFile = `${activeScheduleId}.h264`;
  const outFile = `${activeScheduleId}.mp4`;

  console.log("🎬 Converting...");
  await convert(inFile, outFile);

  console.log("☁️ Uploading...");
  const url = await upload(
    outFile,
    `videos/${activeScheduleId}.mp4`,
    (percent) => {
      events.emit("upload_progress", {
        scheduleId: activeScheduleId,
        percent
      });
    }
  );

  events.emit("recording_complete", {
    scheduleId: activeScheduleId,
    videoUrl: url
  });

  console.log("✅ Upload complete");
  activeScheduleId = null;
};
exports.isRecording = () => {
  return proc !== null;
};
