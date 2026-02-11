const { spawn } = require("child_process");
const convert = require("./converter");
const upload = require("./uploader");
const connection = require("../connection");
const events = require("../events");
let proc = null;
let activeScheduleId = null;
exports.startRecording = ({ scheduleId, arenaId, profile }) => {
  if (proc) {
    console.log("Recording already running");
    return;
  }

  if (!scheduleId) {
    console.error("No scheduleId provided — refusing to record");
    return;
  }

  activeScheduleId = scheduleId;

  console.log("🎥 START RECORDING", { scheduleId, arenaId, profile });

  proc = spawn("rpicam-vid", [
    "--inline",
    "--timeout", "0",
    "-o", `${scheduleId}.h264`
  ]);

  proc.on("exit", () => {
    proc = null;
  });
};
exports.stopRecording = async () => {
  if (!proc) {
    console.log("No active recording");
    return;
  }

  console.log("🛑 STOP RECORDING");
  proc.kill("SIGINT");
  proc = null;

  if (!activeScheduleId) {
    console.error("No active scheduleId — cannot finish recording");
    return;
  }

  const inFile = `${activeScheduleId}.h264`;
  const outFile = `${activeScheduleId}.mp4`;

  // 1️⃣ Convert
  console.log("🎬 Converting to MP4...");
  await convert(inFile, outFile);
  console.log("✅ Conversion complete");

  // 2️⃣ Upload with progress
  console.log("☁️ Uploading...");
  const url = await upload(
    outFile,
    `videos/${activeScheduleId}.mp4`,
    (progress) => {
      connection.send({
  type: "upload_progress",
  scheduleId: activeScheduleId,
  progress
});

    }
  );

  // 3️⃣ Notify backend (via relay)
  
connection.send({
  type: "recording_complete",
  scheduleId: activeScheduleId,
  url
});

  console.log("✅ Upload complete & reported");

  // cleanup
  activeScheduleId = null;
};




  // conversion + relay completion will use activeScheduleId

