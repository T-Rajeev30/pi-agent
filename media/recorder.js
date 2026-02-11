const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const convert = require("./converter");
const upload = require("./uploader");
const events = require("../events");
const config = require("../config");

let proc = null;
let activeScheduleId = null;
let recordingStartedAt = null;
let baseName = null;

/* ================= HELPERS ================= */
async function handlePostProcessing() {
  if (!activeScheduleId) return;

  const inFile = `${activeScheduleId}.h264`;
  const outFile = `${activeScheduleId}.mp4`;

  if (!fs.existsSync(inFile)) {
    console.error("Recording file missing:", inFile);
    return;
  }

  console.log("🎬 Converting...");
  await convert(inFile, outFile);

  console.log("☁️ Uploading...");
  const url = await upload(
    outFile,
    `videos/${activeScheduleId}.mp4`,
    (percent) => {
      events.emit("upload_progress", {
        deviceId: config.DEVICE_ID,
        scheduleId: activeScheduleId,
        percent
      });
    }
  );

  events.emit("recording_complete", {
    deviceId: config.DEVICE_ID,
    scheduleId: activeScheduleId,
    videoUrl: url
  });

  // 🧹 cleanup
  fs.unlinkSync(inFile);
  fs.unlinkSync(outFile);

  console.log("✅ Upload done, files deleted");

  activeScheduleId = null;

  // 🔁 AUTO START NEXT 1-HOUR SLOT
  startNextHour();
}

function getFileBaseName(scheduleId) {
  const now = new Date();
  const date =
    now.getFullYear().toString() +
    String(now.getMonth() + 1).padStart(2, "0") +
    String(now.getDate()).padStart(2, "0");

  const time =
    String(now.getHours()).padStart(2, "0") +
    String(now.getMinutes()).padStart(2, "0") +
    String(now.getSeconds()).padStart(2, "0");

  return `GM_${scheduleId}_${date}_${time}`;
}

/* ================= START RECORDING ================= */

exports.startRecording = ({ scheduleId ,durationMs = 3600000 }) => {
  if (proc) {
    console.log("Recording already running");
    return;
  }

  activeScheduleID = scheduleId;

  if (!scheduleId) {
    console.error("Missing scheduleId");
    return;
  }

  baseName = getFileBaseName(scheduleId);
  activeScheduleId = scheduleId;
  recordingStartedAt = Date.now();

  console.log("🎥 START RECORDING", baseName);

  proc = spawn("rpicam-vid", [
    "--inline",
    "--timeout", String(durationMs),
    "--width", "1280",
    "--height", "720",
    "--framerate", "60",
    "--bitrate", "8000000",
    "-o", `${scheduleId}.h264`
  ]);

  proc.on("exit", async () => {
    console.log("Auto stop triggered");
    proc = null;
    await handlePostProcessing();
  });
};

/* ================= STOP RECORDING ================= */

exports.stopRecording = async () => {
  if (!proc) {
    console.log("No active recording");
    return;
  }

  const elapsed = Date.now() - recordingStartedAt;
  if (elapsed < 3000) {
    console.warn("Recording too short, refusing to stop (<3s)");
    return;
  }

  console.log("🛑 STOP RECORDING");
  proc.kill("SIGINT");
  proc = null;

  const inFile = `${baseName}.h264`;
  const outFile = `${baseName}.mp4`;

  /* ---------- VALIDATE FILE ---------- */
  if (!fs.existsSync(inFile) || fs.statSync(inFile).size === 0) {
    console.error("Recording file empty, aborting upload");
    return;
  }

  /* ---------- CONVERT ---------- */
  console.log("🎬 Converting...");
  await convert(inFile, outFile);

  /* ---------- UPLOAD ---------- */
  console.log("☁️ Uploading...");
  const url = await upload(
    outFile,
    `videos/${outFile}`,
    (percent) => {
      events.emit("upload_progress", {
        deviceId: config.DEVICE_ID,
        scheduleId: activeScheduleId,
        percent: Number(percent)
      });
    }
  );

  /* ---------- COMPLETE ---------- */
  events.emit("recording_complete", {
    deviceId: config.DEVICE_ID,
    scheduleId: activeScheduleId,
    videoUrl: url
  });

  /* ---------- CLEANUP ---------- */
  try {
    fs.unlinkSync(inFile);
    fs.unlinkSync(outFile);
    console.log("🧹 Local files deleted");
  } catch (e) {
    console.error("Cleanup failed:", e.message);
  }

  activeScheduleId = null;
  baseName = null;
  recordingStartedAt = null;

  console.log("✅ Upload complete");
};

/* ================= STATUS ================= */

exports.isRecording = () => proc !== null;
