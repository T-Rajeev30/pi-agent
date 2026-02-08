/**
 * recorder.js
 * MP4 direct recording (NO conversion, demo-safe)
 */

const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

let proc = null;
let currentFile = null;

/**
 * Profiles (extend later)
 */
const PROFILES = {
  "720p60": { width: 1280, height: 720, fps: 60, level: "4.2" },
  "720p30": { width: 1280, height: 720, fps: 30, level: "4.1" },
  "1080p30": { width: 1920, height: 1080, fps: 30, level: "4.2" },
};

/**
 * Start recording
 */
function startRecording({ court = "unknown", profile = "720p60" }) {
  if (proc) {
    throw new Error("Recording already in progress");
  }

  const p = PROFILES[profile];
  if (!p) throw new Error("Invalid profile");

  // Safe filename
  const safeCourt = court.replace(/[^a-zA-Z0-9_-]/g, "_");
  const filename = `arena_${safeCourt}_${Date.now()}.mp4`;
  const outputDir = "/home/pi/videos";
  const output = path.join(outputDir, filename);

  // Ensure directory exists
  fs.mkdirSync(outputDir, { recursive: true });

  const args = [
    "--width", p.width.toString(),
    "--height", p.height.toString(),
    "--framerate", p.fps.toString(),
    "--codec", "h264",
    "--profile", "high",
    "--level", p.level,
    "--inline",        // critical for MP4 stability
    "--timeout", "0",  // run until stopped
    "--output", output
  ];

  proc = spawn("rpicam-vid", args, {
    stdio: ["ignore", "inherit", "inherit"],
  });

  proc.on("exit", (code, signal) => {
    console.log("Recorder exited:", code, signal);
    proc = null;
  });

  proc.on("error", (err) => {
    console.error("Recorder error:", err.message);
    proc = null;
  });

  currentFile = output;

  console.log("Recording started:", output);
  return output;
}

/**
 * Stop recording safely
 */
function stopRecording() {
  if (!proc) {
    console.warn("No active recording");
    return null;
  }

  proc.kill("SIGINT"); // clean MP4 close
  proc = null;

  console.log("Recording stopped");
  return currentFile;
}

/**
 * Recorder status (for dashboard / API)
 */
function getStatus() {
  return {
    recording: !!proc,
    file: currentFile,
  };
}

module.exports = {
  startRecording,
  stopRecording,
  getStatus,
};
