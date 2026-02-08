const { startRecording, stopRecording } = require("./recorder");
const { convertToMP4 } = require("./converter");
const { uploadWithProgress } = require("./uploader");

(async () => {
  console.log("▶ START RECORDING");
  startRecording({ court: "Court_1", profile: "720p30" });

  await new Promise(r => setTimeout(r, 15000));

  console.log("■ STOP RECORDING");
  const h264 = stopRecording();

  console.log("▶ CONVERTING");
  const mp4 = await convertToMP4(h264);

  console.log("▶ UPLOADING");
  const url = await uploadWithProgress(mp4, p =>
    console.log(`UPLOAD ${p.percent}%`)
  );

  console.log("✅ STREAMABLE URL:", url);
})();
