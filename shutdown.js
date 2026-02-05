//Graceful shutdown handling
const logger = require("./logger");
const shell = require("./shell");

function setupShutdown() {
  const shutdown = () => {
    logger.info("Shutting down agent");
    shell.stop();
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

module.exports = setupShutdown;
