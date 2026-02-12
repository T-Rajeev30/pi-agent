const { connectRelay } = require("./connection/relay");
require("./recovery/boot");
require("./upload/worker");
require("./watchdog/disk");
require("./watchdog/process");

console.log("=================================");
console.log("Pi Agent Starting...");
console.log("=================================");

connectRelay();

