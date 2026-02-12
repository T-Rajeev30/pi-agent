const path = require("path");
const fs = require("fs");
const recorder = require("./recorder");
const convert = require("./converter");
const { uploadFile } = require("../upload/uploader");

const STORAGE_DIR = path.join(__dirname, "../storage/temp");

const SEGMENT_DURATION_MS = 15000; // 1 hour

let running = false;

function generateFileName() {
  const now = Date.now();
  return `GM_${now}`;
}

async function processSegment(baseName) {
  const h264 = path.join(STORAGE_DIR, `${baseName}.h264`);
  const mp4 = path.join(STORAGE_DIR, `${baseName}.mp4`);

  try {
    await convert(h264, mp4);

    const url = await uploadFile(
      mp4,
      `videos/${baseName}.mp4`
    );

    console.log("✅ Uploaded:", url);

    // cleanup
    if (fs.existsSync(h264)) fs.unlinkSync(h264);
    if (fs.existsSync(mp4)) fs.unlinkSync(mp4);

    console.log("🧹 Files deleted");
  } catch (err) {
    console.error("❌ Post-processing failed:", err.message);
  }
}

async function startSegmentLoop() {
  if (running) return;
  running = true;

  console.log("🚀 Segmenter started");

  while (running) {
    const baseName = generateFileName();
    const filePath = path.join(STORAGE_DIR, `${baseName}.h264`);

    console.log("🎥 Starting recording:", filePath);

    recorder.startRecording({
      filePath,
      timeout: SEGMENT_DURATION_MS
    });

    // Wait until recording ends
    await recorder.waitForStop();

    console.log("🛑 Segment finished:", baseName);

    await processSegment(baseName);
  }
}

function stopSegmentLoop() {
  running = false;
  recorder.stopRecording();
}

module.exports = {
  startSegmentLoop,
  stopSegmentLoop
};

