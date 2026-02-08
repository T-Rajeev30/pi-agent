const connection = require("./connection");
const recorder = require("./media/recorder");
const config = require("./config");
const logger = require("./logger");

global.__deviceId__ = config.DEVICE_ID;
global.__recorder__ = recorder;

logger.info("====================================");
logger.info("Pi Remote Agent v1.0");
logger.info("====================================");

const ws = connection.connect();

global.__ws__ = ws;

