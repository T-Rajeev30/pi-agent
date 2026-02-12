const { spawn } = require("child_process");

function convert(input, output) {
  return new Promise((resolve, reject) => {
    const ff = spawn("ffmpeg", [
      "-y",
      "-fflags", "+genpts",
      "-r", "60",
      "-i", input,
      "-c:v", "copy",
      "-movflags", "+faststart",
      output
    ]);

    ff.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error("ffmpeg failed"));
    });
  });
}

module.exports = convert;
