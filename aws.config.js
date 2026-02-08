// aws.config.js
module.exports = {
  region: "ap-south-1",

  accessKeyId: process.env.AWS_ACCESS_KEY_ID,
  secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,

  bucket: "statcams-recordings",
};
