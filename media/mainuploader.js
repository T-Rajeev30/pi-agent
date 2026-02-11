const fs = require("fs");
const path = require("path");
const AWS = require("aws-sdk");

AWS.config.update({ region: process.env.AWS_REGION });

const s3 = new AWS.S3({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
});

function uploadWithProgress(filePath, onProgress) {
  return new Promise((resolve, reject) => {
    const fileSize = fs.statSync(filePath).size;
    const stream = fs.createReadStream(filePath);

    const key = `videos/${Date.now()}_${path.basename(filePath)}`;

    const upload = s3.upload({
      Bucket: process.env.AWS_BUCKET,
      Key: key,
      Body: stream,
      ContentType: "video/mp4",
    });

    upload.on("httpUploadProgress", (evt) => {
      const percent = Math.round((evt.loaded / fileSize) * 100);
      onProgress?.({
        status: "UPLOADING",
        percent,
        uploaded: evt.loaded,
        total: fileSize,
      });
    });

    upload.send((err, data) => {
      if (err) return reject(err);
      resolve(data.Location);
    });
  });
}

module.exports = { uploadWithProgress };
