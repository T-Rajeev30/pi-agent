//PTY shell handling
const pty = require("node-pty");
const logger = require("./logger");

let shell = null;

function startShell(onData) {
  shell = pty.spawn("bash", [], {
    name: "xterm-color",
    cols: 80,
    rows: 24,
    cwd: process.env.HOME,
    env: process.env,
  });

  logger.info("Shell started");

  shell.on("data", onData);
}

function write(data) {
  if (shell) shell.write(data);
}

function resize(cols, rows) {
  if (shell) shell.resize(cols, rows);
}

function stop() {
  if (shell) shell.kill();
}

module.exports = {
  startShell,
  write,
  resize,
  stop,
};
