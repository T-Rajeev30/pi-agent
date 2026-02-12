const fs = require("fs");
const path = require("path");
const { uploadWithProgress } = require("./uploader");

const ARCHIVE_DIR = path.join(__dirname, "../storage/archive");

setInterval(async () => {
  const files = fs.readdirSync(ARCHIVE_DIR);

  for (const file of files) {
    if (file.endsWith(".mp4")) {
      try {
        const fullPath = path.join(ARCHIVE_DIR, file);
        await uploadWithProgress(fullPath, `videos/${file}`);
        fs.unlinkSync(fullPath);
        console.log("Retry upload success:", file);
      } catch (err) {
        console.log("Retry failed:", file);
      }
    }
  }
}, 30000);

