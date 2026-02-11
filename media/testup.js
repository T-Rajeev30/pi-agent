const AWS = require("aws-sdk");
const fs = require("fs");
const awsConfig = require("../aws.config");

// 🔒 HARD VALIDATION (fail fast)
if (!awsConfig.bucket) {
  throw new Error("S3 bucket not defined in aws.config.js");
}

if (!awsConfig.accessKeyId || !awsConfig.secretAccessKey) {
  throw new Error("AWS credentials not set in environment");
}

// 🔧 Initialize S3 ONCE
const s3 = new AWS.S3({
  region: awsConfig.region,
  accessKeyId: awsConfig.accessKeyId,
  secretAccessKey: awsConfig.secretAccessKey,
});

/**
 * Upload file with progress callback
 */
module.exports = (filePath, key, onProgress) =>
  new Promise((resolve, reject) => {
    if (!fs.existsSync(filePath)) {
      return reject(new Error("File not found: " + filePath));
    }

    const stream = fs.createReadStream(filePath);

    const upload = s3.upload({
      Bucket: awsConfig.bucket, // ✅ NOW CORRECT
      Key: key,
      Body: stream,
      ContentType: "video/mp4",
    });

    upload.on("httpUploadProgress", (p) => {
      if (onProgress && p.total) {
        const percent = Math.round((p.loaded / p.total) * 100);
        onProgress(percent);
      }
    });

    upload.send((err, data) => {
      if (err) {
        return reject(err);
      }
      resolve(data.Location);
    });
  });

