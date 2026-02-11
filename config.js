// Device config & environment
module.exports = {
  RELAY: "wss://pi-romote-relay.onrender.com",
  DEVICE_ID: "pi-001",
  BACKEND_URL: process.env.BACKEND_URL || "http://10.136.87.64:4000",
  TOKEN: process.env.PI_TOKEN || "super-secret-token"
};
