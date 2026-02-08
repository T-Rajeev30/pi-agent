const { uploadMp4 } = require("./uploader");

(async () => {
  try {
    const url = await uploadMp4(
      "/home/pi/videos/test_720p60_fixed.mp4"
    );
    console.log("UPLOAD SUCCESS");
    console.log("URL:", url);
  } catch (err) {
    console.error("UPLOAD FAILED:", err.message);
  }
})();
