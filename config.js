const path = require("path");

module.exports = {
  TEMP_DIR: path.join(__dirname, "storage/temp"),
  ARCHIVE_DIR: path.join(__dirname, "storage/archive"),
  DEVICE_ID: process.env.DEVICE_ID || "pi-001",
  TOKEN: process.env.PI_TOKEN,
  RELAY: process.env.RELAY_URL,
  AWS_BUCKET: process.env.AWS_BUCKET,
  AWS_REGION: process.env.AWS_REGION,
};

