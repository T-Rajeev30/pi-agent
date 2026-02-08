const recorder = require("./media/recorder");

(async () => {
  recorder.startRecording({
    arenaId: "sanity",
    startTime: "t1",
    endTime: "t2",
    profile: "720p60",
  });

  setTimeout(async () => {
    const url = await recorder.stopRecording();
    console.log("FINAL URL:", url);
    process.exit(0);
  }, 10000);
})();
