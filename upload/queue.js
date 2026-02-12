const fs = require("fs");

const QUEUE_FILE = "./state/upload-queue.json";

function loadQueue() {
  if (!fs.existsSync(QUEUE_FILE)) return [];
  return JSON.parse(fs.readFileSync(QUEUE_FILE));
}

function saveQueue(queue) {
  fs.writeFileSync(QUEUE_FILE, JSON.stringify(queue));
}

function addToQueue(item) {
  const queue = loadQueue();
  queue.push(item);
  saveQueue(queue);
}

module.exports = {
  loadQueue,
  saveQueue,
  addToQueue
};
