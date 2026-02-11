const WebSocket = require("ws");
const recorder = require("./media/recorder");
const config = require("./config");
const logger = require("./logger");

const ws = new WebSocket(config.RELAY_URL);

logger.info("====================================");
logger.info("Pi Remote Agent v1.0 (Relay Mode)");
logger.info(`Device ID: ${config.DEVICE_ID}`);
logger.info("====================================");

ws.on("open", () => {
  logger.info("Connected to relay");
});

ws.on("message", (raw) => {
  let msg;
  try {
    msg = JSON.parse(raw);
  } catch {
    return;
  }

  // Only commands
  if (msg.type !== "command") return;

  // Only for this Pi
  if (msg.deviceId !== config.DEVICE_ID) return;

  if (msg.action === "start_recording") {
    logger.info("START command received via relay");
    recorder.start();
  }

  if (msg.action === "stop_recording") {
    logger.info("STOP command received via relay");
    recorder.stop();
  }
});
