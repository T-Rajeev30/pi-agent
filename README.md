# 🎥 StatCams — Pi Agent

> Raspberry Pi camera agent for the StatCams game film recording system.
> Handles recording, S3 upload, and real-time communication with the backend over MQTT.

---

## ⚡ How It Works
```
[Dashboard]
    │
    │  HTTP → Backend API
    ▼
[Node.js Backend]
    │
    │  MQTT: pi/{id}/command
    ▼
[Pi Agent] ← you are here
    │
    ├── rpicam-vid  → records .h264 + .pts
    ├── ffmpeg      → converts to .mp4 with real timestamps
    └── boto3       → multipart upload to S3
    │
    │  MQTT: pi/{id}/film_status
    ▼
[Backend] → Socket.IO → [Dashboard updated in real-time]
```

---

## 📁 Project Structure
```
pi-agent/
├── main.py              # Entry point — MQTT client, heartbeat, command dispatch
├── recorder.py          # Camera control, ffmpeg conversion, upload trigger
├── camera.py            # Binary detection, disk check, rpicam-vid command builder
├── uploader.py          # S3 multipart upload
├── upload_queue.py      # Persistent retry queue for failed uploads
├── cleanup.py           # Auto-delete oldest videos when disk is low
├── config.example.py    # Config template — copy to config.py and fill in values
└── requirements.txt     # Python dependencies
```

---

## 🔄 Full Recording Lifecycle
```
① MQTT command: start_recording + recordingId
        │
        ▼
② rpicam-vid starts → writes .h264 + .pts (per-frame timestamps)
        │
③ MQTT → film_status: RECORDING
        │
        ▼
④ MQTT command: stop_recording
        │
        ▼
⑤ rpicam-vid terminates gracefully
        │
        ▼
⑥ ffmpeg converts .h264 → .mp4
   • If .pts valid  → real wall-clock timestamps preserved
   • If .pts bad    → sequential timestamps at target fps
        │
③ MQTT → film_status: PROCESSING
        │
        ▼
⑦ boto3 multipart upload → S3
        │
        ▼
⑧ MQTT → film_status: COMPLETED + s3Url
        │
        ▼
⑨ Local .mp4 deleted (if DELETE_AFTER_UPLOAD = True)
```

---

## 📡 MQTT Topics

| Topic | Direction | Payload | Description |
|-------|-----------|---------|-------------|
| `pi/{deviceId}/command` | Server → Pi | `{ command, recordingId }` | Start / stop trigger |
| `pi/{deviceId}/heartbeat` | Pi → Server | `{ deviceId, name, status }` | Keepalive every 5s |
| `pi/{deviceId}/film_status` | Pi → Server | `{ status, recordingId, s3Url? }` | Progress updates |

### Commands

| Command | Description |
|---------|-------------|
| `start_recording` | Begin recording — requires `recordingId` |
| `stop_recording` | Stop recording and begin processing |

### Film Status Values

| Status | Meaning |
|--------|---------|
| `RECORDING` | Camera is actively recording |
| `PROCESSING` | ffmpeg converting h264 → mp4 |
| `UPLOADING` | Uploading to S3 |
| `COMPLETED` | Upload done — s3Url available |
| `FAILED` | Something went wrong |

---

## ⚙️ Setup

### 1. Clone
```bash
git clone https://github.com/T-Rajeev30/pi-agent.git
cd pi-agent
```

### 2. Install system dependencies
```bash
sudo apt update
sudo apt install ffmpeg rpicam-apps -y
```

### 3. Install Python dependencies
```bash
pip3 install -r requirements.txt
```

### 4. Configure
```bash
cp config.example.py config.py
nano config.py
```

Fill in:
- `DEVICE_ID` — unique ID for this Pi (e.g. `pi-001`)
- `MQTT_BROKER` — your EC2 server IP
- `AWS_ACCESS_KEY`, `AWS_SECRET_KEY`, `AWS_REGION`, `AWS_BUCKET`

### 5. Run
```bash
python3 main.py
```

---

## 🚀 Run on Boot (systemd)
```bash
sudo nano /etc/systemd/system/pi-agent.service
```

Paste:
```ini
[Unit]
Description=StatCams Pi Agent
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/pi-agent/main.py
WorkingDirectory=/home/pi/pi-agent
Restart=always
RestartSec=5
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-agent
sudo systemctl start pi-agent
sudo systemctl status pi-agent
```

View logs:
```bash
journalctl -u pi-agent -f
```

---

## 🔧 Config Reference

| Key | Description | Default |
|-----|-------------|---------|
| `DEVICE_ID` | Unique Pi identifier | `pi-001` |
| `DEVICE_NAME` | Display name on dashboard | `Court Camera 1` |
| `MQTT_BROKER` | EC2 server IP | — |
| `MQTT_PORT` | MQTT port | `1883` |
| `CAMERA_WIDTH` | Recording width px | `1280` |
| `CAMERA_HEIGHT` | Recording height px | `720` |
| `CAMERA_FRAMERATE` | FPS | `30` |
| `VIDEO_BITRATE` | Bitrate bps | `4000000` |
| `MIN_FREE_DISK_MB` | Min free disk before cleanup | `500` |
| `DELETE_AFTER_UPLOAD` | Delete local file post-upload | `True` |
| `UPLOAD_RETRY_INTERVAL` | Retry failed uploads every N seconds | `60` |
| `HEARTBEAT_INTERVAL` | Heartbeat frequency seconds | `5` |

---

## 🩺 Troubleshooting

| Problem | Fix |
|---------|-----|
| `rpicam-vid not found` | `sudo apt install rpicam-apps` |
| `ffmpeg not found` | `sudo apt install ffmpeg` |
| Camera not detected | `rpicam-hello` to test camera |
| MQTT not connecting | Check EC2 IP and port 1883 is open in security group |
| Upload failing | Check AWS credentials and bucket policy |
| Short recording duration | pts file missing — check disk space |

---

## 👤 Author

Built by [@T-Rajeev30](https://github.com/T-Rajeev30)

---

> *StatCams — Because every play matters.*
