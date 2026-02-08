const { spawn } = require("child_process");

const TRANSCODE_PROFILES = {
  "720p60": {
    fps: 60,
    level: "4.2",
    bitrate: "6M",
    bufsize: "12M",
    gop: 120,
  },
  "720p30": {
    fps: 30,
    level: "4.1",
    bitrate: "4M",
    bufsize: "8M",
    gop: 60,
  },
  "1080p30": {
    fps: 30,
    level: "4.2",
    bitrate: "8M",
    bufsize: "16M",
    gop: 60,
  },
};

function transcodeToMp4({ inputPath, profile }) {
  return new Promise((resolve, reject) => {
    const p = TRANSCODE_PROFILES[profile];
    if (!p) return reject(new Error("Invalid transcode profile"));

    const outputPath = inputPath.replace(".h264", `_stream_${profile}.mp4`);

    const args = [
      "-y",
      "-framerate", p.fps.toString(),
      "-i", inputPath,
      "-c:v", "libx264",
      "-preset", "fast",
      "-profile:v", "high",
      "-level", p.level,
      "-pix_fmt", "yuv420p",
      "-b:v", p.bitrate,
      "-maxrate", p.bitrate,
      "-bufsize", p.bufsize,
      "-g", p.gop.toString(),
      "-keyint_min", p.gop.toString(),
      "-sc_threshold", "0",
      "-movflags", "+faststart",
      outputPath,
    ];

    const ff = spawn("ffmpeg", args, { stdio: "inherit" });

    ff.on("close", (code) => {
      if (code === 0) resolve(outputPath);
      else reject(new Error("FFmpeg failed"));
    });
  });
}

module.exports = { transcodeToMp4 };
