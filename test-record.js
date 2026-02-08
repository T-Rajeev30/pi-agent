const recorder = require("./media/recorder");

(async () => {
  try {
    console.log("Starting recording...");

    recorder.startRecording({
      arenaId: "court1",
      startTime: "10_00",
      endTime: "10_10",
      profile: "720p60",
    });

    // Record for 10 seconds
    setTimeout(async () => {
      console.log("Stopping recording...");
      const url = await recorder.stopRecording();
      console.log("FINAL VIDEO URL:", url);
      process.exit(0);
    }, 10000);

  } catch (err) {
    console.error("TEST FAILED:", err.message);
    process.exit(1);
  }
})();

