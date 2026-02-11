const fetch = require("node-fetch");
const config = require("./config");
const recorder = require("./media/recorder");
const logger = require("./logger");

// init relay connection
require("./connection");

logger.info("====================================");
logger.info("Pi Remote Agent v1.0");
logger.info(`Device ID: ${config.DEVICE_ID}`);
logger.info("====================================");

// HEARTBEAT → backend
setInterval(async () => {
  try {
    await fetch(`${config.BACKEND_URL}/api/devices/heartbeat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        deviceId: config.DEVICE_ID,
        status: recorder.isRecording() ? "PROGRESS" : "STANDBY",
        recording: recorder.isRecording(),
      }),
    });
  } catch (err) {
    logger.error("Heartbeat failed:", err.message);
  }
}, 5000);

