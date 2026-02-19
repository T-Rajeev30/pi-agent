/**
 * uploader.js
 *
 * Uploads large video files to S3 using multipart upload.
 * Uses the filename provided by recorder.js so naming is preserved.
 */

require("dotenv").config();
const AWS = require("aws-sdk");
const fs = require("fs");
const path = require("path");

/* Configure AWS */
AWS.config.update({
  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
  region: process.env.AWS_REGION
});

/* Multipart upload configuration (important for long recordings) */
const s3 = new AWS.S3({
  partSize: 64 * 1024 * 1024, // 64MB chunks
  queueSize: 4
});

/**
 * Upload file to S3
 *
 * @param {string} filePath  - Local file path
 * @param {string} fileName  - Desired S3 filename
 */
exports.uploadLarge = (filePath, fileName) => {

  /* fallback safety */
  if (!fileName) {
    fileName = path.basename(filePath);
  } const key = `videos/device_name/${fileName}`;

  console.log("Uploading as:", key);

  const stream = fs.createReadStream(filePath);

  return new Promise((resolve, reject) => {

    s3.upload({
      Bucket: process.env.AWS_BUCKET,
      Key: key,
      Body: stream,
      ContentType: "video/mp4"
    })
    .on("httpUploadProgress", progress => {
      if (progress.total) {
        const percent = Math.round((progress.loaded / progress.total) * 100);
        console.log(`Upload ${percent}%`);
      }
    })
    .send((err, data) => {
      if (err) return reject(err);
      resolve(data.Location);
    });
  });
};









