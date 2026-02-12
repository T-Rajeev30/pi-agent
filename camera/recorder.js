const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const convert = require("./converter");
const { uploadWithProgress } = require("../upload/uploader");

const STORAGE_DIR = path.join(__dirname, "../storage/temp");

let proc = null;
let recording = false;

/* ================= INIT ================= */

if (!fs.existsSync(STORAGE_DIR)) {
  fs.mkdirSync(STORAGE_DIR, { recursive: true });
}

/* ================= START RECORDING ================= */

function startRecording(durationMinutes = 60, progressCb = () => {}, testSeconds = null) {
  if (proc) {
    return Promise.reject(new Error("Recording already running"));
  }

  return new Promise((resolve, reject) => {
    const ts = Date.now();
    const base = `GM_${ts}`;

    const h264 = path.join(STORAGE_DIR, `${base}.h264`);
    const mp4 = path.join(STORAGE_DIR, `${base}.mp4`);

    const timeoutMs = testSeconds
      ? testSeconds * 1000
      : durationMinutes * 60 * 1000;

    console.log(testSeconds
      ? `TEST MODE → ${testSeconds}s recording`
      : `Recording ${durationMinutes} minute(s)`);

    recording = true;

    proc = spawn("rpicam-vid", [
      "--codec", "h264",
      "--inline",
      "--nopreview",
      "--width", "1280",
      "--height", "720",
      "--framerate", "60",
      "--profile", "high",
      "--level", "4.2",
      "--bitrate", "6000000",
      "--intra", "60",
      "--denoise", "off",
      "--timeout", timeoutMs.toString(),
      "-o", h264
    ]);

    proc.on("error", (err) => {
      recording = false;
      proc = null;
      reject(new Error("Failed to start rpicam-vid. Is camera enabled?"));
    });

    proc.on("close", async (code) => {
      proc = null;
      recording = false;

      if (code !== 0) {
        return reject(new Error("Recording process exited with error"));
      }

      try {
        console.log("Remux → MP4");
        await convert(h264, mp4);

        console.log("Uploading...");
        const url = await uploadWithProgress(
          mp4,
          `videos/${base}.mp4`,
          progressCb
        );

        fs.unlinkSync(h264);
        fs.unlinkSync(mp4);

        console.log("Upload complete:", url);
        resolve(url);
      } catch (err) {
        reject(err);
      }
    });
  });
}

/* ================= STOP ================= */

function stopRecording() {
  if (proc) {
    console.log("Stopping recording...");
    proc.kill("SIGINT");
  }
}

/* ================= STATE ================= */

function isRecording() {
  return recording;
}

/* ================= EXPORT ================= */

module.exports = {
  startRecording,
  stopRecording,
  isRecording
};
