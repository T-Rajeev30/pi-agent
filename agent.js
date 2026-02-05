const shell = require("./shell");
const connection = require("./connection");
const shutdown = require("./shutdown");
const logger = require("./logger");

logger.info("====================================");
logger.info("Pi Remote Agent v1.0");
logger.info("====================================");

shutdown();

const ws = connection.connect((data) => {
  ws.send({ type: "output", data });
});

shell.startShell((data) => {
  ws.send({ type: "output", data });
});
