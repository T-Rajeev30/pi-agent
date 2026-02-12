const { exec } = require("child_process");

setInterval(() => {
  exec("df -h /", (err, stdout) => {
    if (err) return;

    const lines = stdout.split("\n");
    const data = lines[1].split(/\s+/);

    const usedPercent = parseInt(data[4].replace("%", ""));

    if (usedPercent > 95) {
      console.error("CRITICAL: Disk almost full");
    }
  });
}, 60000);

