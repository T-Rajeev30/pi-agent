const recorder = require("./media/recorder");

(async () => {
  recorder.startRecording({ court: "Court 1", profile: "720p60" });

  setTimeout(async () => {
    const file = await recorder.stopRecording();
    console.log("FINAL FILE:", file);
    process.exit(0);
  }, 15000);
})();
 
