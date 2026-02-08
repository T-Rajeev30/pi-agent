const { startRecording, stopRecording } = require("./media/recorder");

(async () => {
  const file = startRecording({ court: "Court1", profile: "720p60" });
  console.log("Recording:", file);

  setTimeout(() => {
    const out = stopRecording();
    console.log("Stopped:", out);
  }, 5000);
})();

