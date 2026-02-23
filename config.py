DEVICE_ID        = "pi-001"
DEVICE_NAME      = "Court Camera 1"
MQTT_BROKER      = "13.203.194.90"
MQTT_PORT        = 1883
MQTT_KEEPALIVE   = 60
VIDEO_DIR        = "/home/pi/videos"
CAMERA_WIDTH     = 1280
CAMERA_HEIGHT    = 720
CAMERA_FRAMERATE = 60
VIDEO_CODEC = "h264"
VIDEO_BITRATE = 6000000   # 6 Mbps (good quality for 720p60)
S3_PREFIX        = "videos/pi-001/"
MIN_FREE_DISK_MB = 500
S3_CHUNK_SIZE    = 8 * 1024 * 1024
HEARTBEAT_INTERVAL = 5
# Storage cleanup behavior

DELETE_AFTER_UPLOAD = True        # delete file after successful upload
DELETE_FAILED_UPLOADS = False     # delete file if upload fails
UPLOAD_RETRY_INTERVAL = 60      # seconds between retry attempts
UPLOAD_QUEUE_FILE = "/home/pi/pi-agent/upload_queue.json"
# S3 folder structure
S3_ROOT_FOLDER = "StatsCams_Recording"

AWS_ACCESS_KEY=""
AWS_SECRET_KEY=""
AWS_REGION=""
AWS_BUCKET=""
