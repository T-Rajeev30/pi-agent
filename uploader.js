const fs = require("fs");
const path = require("path");
const AWS = require("aws-sdk");

// AWS config via env
const s3 = new AWS.S3({
  region: process.env.AWS_REGION,
});

let uploadState = {
  status: "IDLE",     // IDLE | UPLOADING | DONE | ERROR
  percent: 0,
  uploaded: 0,
  total: 0,
  url: null,
};

/**
 * Upload file with progress
 */
function uploadWithProgress(filePath) {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(filePath)) {
      return reject(new Error("File not found"));
    }

    const fileSize = fs.statSync(filePath).size;
    uploadState = {
      status: "UPLOADING",
      percent: 0,
      uploaded: 0,
      total: fileSize,
      url: null,
    };

    const key = `videos/${Date.now()}_${path.basename(filePath)}`;

    const upload = s3.upload({
      Bucket: process.env.AWS_BUCKET,
      Key: key,
      Body: fs.createReadStream(filePath),
      ContentType: "video/mp4",
    });

    upload.on("httpUploadProgress", (evt) => {
      uploadState.uploaded = evt.loaded;
      uploadState.total = fileSize;
      uploadState.percent = Math.round(
        (evt.loaded / fileSize) * 100
      );

      // OPTIONAL: log every 10%
      if (uploadState.percent % 10 === 0) {
        console.log(
          `Upload ${uploadState.percent}% (${evt.loaded}/${fileSize})`
        );
      }
    });

    upload.send((err, data) => {
      if (err) {
        uploadState.status = "ERROR";
        return reject(err);
      }

      uploadState.status = "DONE";
      uploadState.url = data.Location;
      resolve(data.Location);
    });
  });
}

/**
 * For dashboard polling
 */
function getUploadStatus() {
  return uploadState;
}

module.exports = {
  uploadWithProgress,
  getUploadStatus,
};
