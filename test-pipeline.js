const recorder = require("./camera/recorder");
const convert = require("./camera/converter");
const { uploadFile } = require("./upload/uploader");

async function run() {
  const name = "GM_" + Date.now();

  recorder.startRecording(name);

  await new Promise(r => setTimeout(r, 10000));

  const h264 = await recorder.stopRecording();

  const mp4 = h264.replace(".h264", ".mp4");

  await convert(h264, mp4);

  const url = await uploadFile(
    mp4,
    `videos/${name}.mp4`
  );

  console.log("FINAL URL:", url);
}

run();
