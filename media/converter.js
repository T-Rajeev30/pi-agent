const { spawn } = require("child_process");
const path = require("path");

function convertToMP4(h264Path) {
  return new Promise((resolve, reject) => {
    if (!h264Path.endsWith(".h264")) {
      return reject(new Error("Input must be .h264"));
    }

    const mp4Path = h264Path.replace(".h264", ".mp4");

    const args = [
      "-y",
      "-fflags", "+genpts", // FIX timestamps
      "-r", "30",           // FORCE CFR (match recorder)
      "-i", h264Path,
      "-map", "0:v:0",
      "-c:v", "copy",       // NO re-encode
      "-movflags", "+faststart",
      mp4Path,
    ];

    const ff = spawn("ffmpeg", args, { stdio: "inherit" });

    ff.on("exit", (code) => {
      if (code === 0) {
        console.log("Converted to MP4:", mp4Path);
        resolve(mp4Path);
      } else {
        reject(new Error("ffmpeg failed"));
      }
    });
  });
}

module.exports = { convertToMP4 };
