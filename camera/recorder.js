/**
 * recorder.js
 *
 * Controls camera recording lifecycle.
 * Naming format:
 * GM_DD_MM_YYYY_FROM_STARTTIME_TO_ENDTIME.mp4
 */

const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const convert = require("./converter");
const { uploadLarge } = require("../upload/uploader");

const STORAGE = path.join(__dirname, "../storage");
if (!fs.existsSync(STORAGE)) fs.mkdirSync(STORAGE);

/* recording state */
let proc = null;
let recording = false;

/* time tracking */
let startTime = null;
let baseDate = null;

/* helpers */
function pad(n) {
  return n.toString().padStart(2, "0");
}

function formatDate(d) {
  return `${pad(d.getDate())}_${pad(d.getMonth() + 1)}_${d.getFullYear()}`;
}

function formatTime(d) {
  return `${pad(d.getHours())}-${pad(d.getMinutes())}-${pad(d.getSeconds())}`;
}
/**
 * Start recording (runs until STOP command)
 */
exports.startRecording = () => {
  if (proc) throw new Error("Already recording");

  startTime = new Date();
  baseDate = formatDate(startTime);

  const startStr = formatTime(startTime);

  const h264Path = path.join(
    STORAGE,
    `GM_${baseDate}_FROM_${startStr}.h264`
  );

  console.log("Recording started:", h264Path);
  recording = true;

  proc = spawn("rpicam-vid", [
    "--codec", "h264",
    "--timeout", "0",              // unlimited recording

    "--width", "1280",
    "--height", "720",
    "--framerate", "60",

    "--bitrate", "6000000",
    "--profile", "high",
    "--level", "4.2",
    "--intra", "60",

    "--denoise", "off",
    "--inline",
    "--nopreview",
    "-o", h264Path
  ]);

  proc.stderr.on("data", d => console.log("[CAMERA]", d.toString()));

  return new Promise((resolve, reject) => {

    proc.on("close", async () => {
      recording = false;
      proc = null;

      try {
        const endTime = new Date();
        const endStr = formatTime(endTime);

        const mp4Path = path.join(
          STORAGE,
          `GM_${baseDate}_FROM_${formatTime(startTime)}_TO_${endStr}.mp4`
        );

        console.log("Recording stopped");
        console.log("Final file:", mp4Path);

        /* Convert raw stream to MP4 container */
        await convert(h264Path, mp4Path);

        /* Send filename explicitly to uploader */
        const finalName = path.basename(mp4Path);
        const url = await uploadLarge(mp4Path, finalName);

        /* Cleanup temp files */
        fs.unlinkSync(h264Path);
        fs.unlinkSync(mp4Path);

        resolve(url);
        } catch (err) {
        reject(err);
      }
    });
  });
};

/**
 * Stop recording manually
 */
exports.stopRecording = () => {
  if (proc) {
    console.log("Stopping recording...");
    proc.kill("SIGINT");
  }
};

/**
 * Used for heartbeat status
 */
exports.isRecording = () => recording;
