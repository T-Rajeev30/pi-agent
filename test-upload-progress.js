const { uploadWithProgress, getUploadStatus } = require("./uploader");

(async () => {
  try {
    const file = "/home/pi/videos/arena_Court_1_1770555999430.mp4"; // replace with real file

    const interval = setInterval(() => {
      console.log("STATUS:", getUploadStatus());
    }, 1000);

    const url = await uploadWithProgress(file);
    clearInterval(interval);

    console.log("UPLOAD COMPLETE:", url);
  } catch (err) {
    console.error("UPLOAD FAILED:", err.message);
  }
})();
