<<<<<<< HEAD:config.example.py
DEVICE_ID        = "pi-002"
DEVICE_NAME      = "Court Camera 1"
=======
import os

# ── Device Identity ────────────────────────────────────────────────────────────
DEVICE_ID   = "cn-pz-001"
DEVICE_NAME = "Court Camera 1"
COURT_FIELD = "court-001"
# ── MQTT ──────────────────────────────────────────────────────────────────────
>>>>>>> c895842 (Improve recording stability, queue reliability, and device sync):config.py
MQTT_BROKER      = "13.203.194.90"
MQTT_PORT        = 1883
MQTT_KEEPALIVE   = 60

# ── Video Storage ─────────────────────────────────────────────────────────────
VIDEO_DIR        = "/home/pi/videos"
CAMERA_WIDTH     = 1280
CAMERA_HEIGHT    = 720
CAMERA_FRAMERATE = 30
VIDEO_CODEC      = "h264"
VIDEO_BITRATE    = 4000000
MIN_FREE_DISK_MB = 500

# ── S3 Upload ─────────────────────────────────────────────────────────────────
S3_PREFIX        = f"videos/{DEVICE_ID}"
S3_CHUNK_SIZE    = 8 * 1024 * 1024
S3_ROOT_FOLDER   = "StatsCams_Recording"

# ✅ SECURITY FIX: Load AWS credentials from environment variables, NOT hardcoded.
# Set these in /etc/environment or a .env file (never commit credentials to git).
# To set: export AWS_ACCESS_KEY="your_key"  export AWS_SECRET_KEY="your_secret"
AWS_ACCESS_KEY   = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY   = os.environ.get("AWS_SECRET_KEY")
AWS_REGION       = os.environ.get("AWS_REGION", "ap-south-1")
AWS_BUCKET       = os.environ.get("AWS_BUCKET", "statslane-newdata")

if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
    raise EnvironmentError(
        "[Config] AWS_ACCESS_KEY and AWS_SECRET_KEY must be set as environment variables. "
        "Never hardcode credentials in config.py."
    )

# ── Upload Behavior ───────────────────────────────────────────────────────────
HEARTBEAT_INTERVAL    = 5
DELETE_AFTER_UPLOAD   = True
DELETE_FAILED_UPLOADS = False
UPLOAD_RETRY_INTERVAL = 60
UPLOAD_QUEUE_FILE     = "/home/pi/pi-agent/upload_queue.json"
<<<<<<< HEAD:config.example.py

# S3 folder structure
S3_ROOT_FOLDER = "StatsCams_Recording"
AWS_ACCESS_KEY=""
AWS_SECRET_KEY=""
AWS_REGION=""
AWS_BUCKET=""

=======
>>>>>>> c895842 (Improve recording stability, queue reliability, and device sync):config.py
