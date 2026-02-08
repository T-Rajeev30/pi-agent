const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

let proc = null;
let currentFile = null;

const PROFILES = {
  "720p30": { width: 1280, height: 720, fps: 30, level: "4.1", intra: 30 },
  "720p60": { width: 1280, height: 720, fps: 60, level: "4.2", intra: 30 },
};

function startRecording({ court = "unknown", profile = "720p30" }) {
  if (proc) throw new Error("Already recording");

  const p = PROFILES[profile];
  if (!p) throw new Error("Invalid profile");

  if (!fs.existsSync("/home/pi/videos")) {
    fs.mkdirSync("/home/pi/videos", { recursive: true });
  }

  const safeCourt = court.replace(/[^a-zA-Z0-9_-]/g, "_");
  const filename = `arena_${safeCourt}_${Date.now()}.h264`;
  const output = path.join("/home/pi/videos", filename);

  const args = [
    "--width", String(p.width),
    "--height", String(p.height),
    "--framerate", String(p.fps),
    "--codec", "h264",
    "--profile", "high",
    "--level", p.level,
    "--inline",                 // SPS/PPS inline
    "--intra", String(p.intra), // KEYFRAMES (CRITICAL)
    "--timeout", "0",
    "--output", output,
  ];

  proc = spawn("rpicam-vid", args, { stdio: "inherit" });
  currentFile = output;

  console.log("Recording started:", output);
  return output;
}

function stopRecording() {
  if (!proc) return null;
  proc.kill("SIGINT");
  proc = null;
  console.log("Recording stopped");
  return currentFile;
}

function getStatus() {
  return {
    recording: !!proc,
    file: currentFile,
  };
}

module.exports = { startRecording, stopRecording, getStatus };
