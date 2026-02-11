const { exec } = require("child_process");

module.exports = (input, output) =>
  new Promise((resolve, reject) => {
    exec(`ffmpeg -y -i ${input} -c copy ${output}`, (err) => {
      if (err) reject(err);
      else resolve();
    });
  });

