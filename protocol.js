//Message routing (input/output)
const shell = require("./shell");

function handleMessage(msg) {
  if (msg.type === "input") {
    shell.write(msg.data);
  }

  if (msg.type === "resize") {
    shell.resize(msg.cols, msg.rows);
  }
}

module.exports = { handleMessage };
