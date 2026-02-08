const recorder = require("./media/recorder");

(async () => {
  try {
    console.log("STARTING RECORDING");
    recorder.startRecording({
      arenaId: "direct",
      startTime: "now",
      endTime: "later",
      profile: "720p60",
    });

    setTimeout(async () => {
      console.log("STOPPING RECORDING");
      const url = await recorder.stopRecording();
      console.log("SUCCESS, URL:", url);
      process.exit(0);
    }, 8000);

  } catch (e) {
    console.error("FAILED:", e.message);
    process.exit(1);
  }
})();
