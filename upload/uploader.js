require("dotenv").config();
const AWS = require("aws-sdk");
const fs = require("fs");

AWS.config.update({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION
});

const s3 = new AWS.S3();

function uploadWithProgress(filePath, key, onProgress = () => {}) {
  return new Promise((resolve, reject) => {

    const size = fs.statSync(filePath).size;

    const upload = s3.upload({
      Bucket: process.env.AWS_BUCKET,
      Key: key,
      Body: fs.createReadStream(filePath),
      ContentType: "video/mp4"
    });

    upload.on("httpUploadProgress", (evt) => {
      const percent = Math.round((evt.loaded / size) * 100);
      process.stdout.write(`Upload ${percent}%\r`);
      onProgress(percent);
    });

    upload.send((err, data) => {
      if (err) return reject(err);
      resolve(data.Location);
    });
  });
}

module.exports = { uploadWithProgress };
