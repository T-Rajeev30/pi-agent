const { spawn } = require("child_process");

module.exports = (input, output) => {
  return new Promise((resolve, reject) => {
    const ff = spawn("ffmpeg", [
      "-y",
      "-fflags", "+genpts",
      "-i", input,
      "-c", "copy",
      "-movflags", "+faststart",
      output
    ]);

    ff.on("close", code => {
      if (code === 0) resolve();
      else reject(new Error("ffmpeg failed"));
    });
  });
};
