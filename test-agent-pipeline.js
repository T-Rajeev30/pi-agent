const recorder = require("./camera/recorder");

async function runTest() {
  const scheduleId = "TEST_" + Date.now();

  console.log("===== PIPELINE TEST START =====");
  console.log("Schedule:", scheduleId);

  recorder.startRecording({ scheduleId });

  // record for 5 seconds
  await new Promise(r => setTimeout(r, 5000));

  const url = await recorder.stopRecording();

  console.log("FINAL URL:", url);
  console.log("===== PIPELINE TEST COMPLETE =====");
}

runTest();

