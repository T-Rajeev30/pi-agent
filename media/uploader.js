const AWS = require("aws-sdk");
const fs = require("fs");
const awsConfig = require("../aws.config");

AWS.config.update({
  region: awsConfig.region,
  accessKeyId: awsConfig.accessKeyId,
  secretAccessKey: awsConfig.secretAccessKey,
});

const s3 = new AWS.S3();

module.exports = (filePath, key, onProgress) =>
  new Promise((resolve, reject) => {
    console.log("📦 Upload init");
    console.log("File:", filePath);
    console.log("Bucket:", awsConfig.bucket);
    console.log("Key:", key);

    const size = fs.statSync(filePath).size;
    console.log("File size:", size, "bytes");

    const upload = s3.upload(
      {
        Bucket: awsConfig.bucket,
        Key: key,
        Body: fs.createReadStream(filePath),
        ContentType: "video/mp4",
      },
      {
        partSize: 5 * 1024 * 1024, // 🔴 FORCE multipart
        queueSize: 1,
      }
    );

    upload.on("httpUploadProgress", (p) => {
      console.log("📡 RAW PROGRESS EVENT:", p);

      if (!p.total) return;

      const percent = Math.round((p.loaded / p.total) * 100);
      console.log(`⬆️ Upload ${percent}%`);

      if (onProgress) onProgress(percent);
    });

    upload.send((err, data) => {
      if (err) {
        console.error("❌ Upload error:", err);
        reject(err);
      } else {
        console.log("✅ Upload finished:", data.Location);
        resolve(data.Location);
      }
    });
  });
