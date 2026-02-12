const { uploadFile } = require("./upload/uploader");

async function run() {
  const url = await uploadFile(
    "storage/temp/test.mp4",
    "videos/test.mp4"
  );

  console.log("Uploaded:", url);
}

run();

