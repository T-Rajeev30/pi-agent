# 🤖 Pi Agent

<div align="center">

[![GitHub stars](https://img.shields.io/github/stars/T-Rajeev30/pi-agent?style=for-the-badge)](https://github.com/T-Rajeev30/pi-agent/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/T-Rajeev30/pi-agent?style=for-the-badge)](https://github.com/T-Rajeev30/pi-agent/network)
[![GitHub issues](https://img.shields.io/github/issues/T-Rajeev30/pi-agent?style=for-the-badge)](https://github.com/T-Rajeev30/pi-agent/issues)
[![Python version](https://img.shields.io/badge/Python-3.x-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

**A lightweight, configurable Python agent designed for Raspberry Pi to perform scheduled data capture and secure remote uploads.**

</div>

## 📖 Overview

The Pi Agent is a dedicated backend service crafted for Raspberry Pi devices, enabling autonomous data collection and synchronized uploading to a remote server. It's built to run continuously in the background, leveraging the Pi's hardware capabilities to record specific types of data (e.g., video, images) at predefined intervals and securely transmit them. This project is ideal for surveillance, environmental monitoring, or remote data logging applications where a Raspberry Pi acts as an edge device.

## ✨ Features

- **Automated Data Capture**: Configurable modules for interacting with Raspberry Pi camera and other sensors (e.g., GPIO).
- **Scheduled Tasks**: Utilizes a flexible scheduling mechanism to run recording and uploading tasks at set intervals.
- **Secure Remote Uploads**: Efficiently uploads captured data to a specified API endpoint using HTTP requests.
- **Robust Configuration**: Easily manage agent settings through a dedicated `config.py` file and environment variables.
- **Modular Design**: Separated concerns for camera operations, recording logic, and uploading, making it extensible.
- **Comprehensive Logging**: Integrates Python's standard logging module for detailed operation monitoring and debugging.
- **Resource Efficient**: Designed to run effectively on Raspberry Pi's limited resources.

## 🛠️ Tech Stack

**Runtime:**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

**Core Libraries:**

![Requests](https://img.shields.io/badge/Requests-black?style=for-the-badge&logo=python&logoColor=white)
![python-dotenv](https://img.shields.io/badge/python--dotenv-blueviolet?style=for-the-badge&logo=python&logoColor=white)
![schedule](https://img.shields.io/badge/schedule-green?style=for-the-badge&logo=python&logoColor=white)

**Hardware-Specific Libraries (Raspberry Pi):**

![picamera](https://img.shields.io/badge/picamera-red?style=for-the-badge&logo=raspberrypi&logoColor=white)
![RPi.GPIO](https://img.shields.io/badge/RPi.GPIO-orange?style=for-the-badge&logo=raspberrypi&logoColor=white)

## 🚀 Quick Start

Follow these steps to get your Pi Agent up and running on your Raspberry Pi.

### Prerequisites

- **Raspberry Pi**: Any model compatible with `picamera` and `RPi.GPIO` (e.g., Pi 3, Pi 4).
- **Raspberry Pi Camera Module**: Required for camera functionalities.
- **Python 3.x**: Recommended Python version 3.7 or higher.
- **pip**: Python package installer.
- **Git**: For cloning the repository.

### Installation

1. **Clone the repository**
    ```bash
    git clone https://github.com/T-Rajeev30/pi-agent.git
    cd pi-agent
    ```

2. **Create and activate a virtual environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4. **Environment setup**
    ```bash
    cp .env.example .env
    ```
    Open the newly created `.env` file and configure your environment variables:
    ```ini
    # .env
    API_URL="http://your-remote-server.com/api/upload"
    DEVICE_ID="my_raspberry_pi_01"
    API_KEY="your_secret_api_key"
    VIDEO_STORAGE_PATH="/home/pi/pi_agent_data/videos"
    IMAGE_STORAGE_PATH="/home/pi/pi_agent_data/images"
    ```
    > **Note**: Create storage directories if they don't exist:
    > ```bash
    > mkdir -p /home/pi/pi_agent_data/videos
    > mkdir -p /home/pi/pi_agent_data/images
    > ```

5. **Start the agent**
    ```bash
    python3 main.py
    ```

## 📁 Project Structure

```
pi-agent/
├── camera.py       # Module for camera control and media capture
├── config.py       # Centralized configuration loader and settings
├── main.py         # Main entry point and orchestrator for agent tasks
├── recorder.py     # Module for managing recording sessions (video/image)
├── uploader.py     # Module for uploading captured data to remote server
└── requirements.txt # Python dependency list
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|---|---|---|---|
| `API_URL` | URL of the remote API endpoint for data uploads. | `http://localhost:8000/upload` | Yes |
| `DEVICE_ID` | A unique identifier for the Raspberry Pi agent. | `pi-agent-default` | Yes |
| `API_KEY` | Optional API key for authenticating with the remote server. | `None` | No |
| `VIDEO_STORAGE_PATH` | Local path to temporarily store video recordings. | `/tmp/pi_agent_videos` | Yes |
| `IMAGE_STORAGE_PATH` | Local path to temporarily store image captures. | `/tmp/pi_agent_images` | Yes |
| `RECORD_INTERVAL_SECONDS` | Interval (in seconds) between scheduled recording tasks. | `60` | No |
| `UPLOAD_INTERVAL_SECONDS` | Interval (in seconds) between scheduled upload tasks. | `300` | No |
| `LOG_LEVEL` | Logging level (e.g., `INFO`, `DEBUG`, `WARNING`). | `INFO` | No |

### Configuration File (`config.py`)

The `config.py` file centralizes the loading of environment variables and provides them as easily accessible constants throughout the application. It also defines default values if environment variables are not set.

## 🔧 Development

### Running the Agent

```bash
source venv/bin/activate
python3 main.py
```

### Logging

Adjust the `LOG_LEVEL` environment variable to control verbosity of logs printed to the console.

## 🚀 Deployment

### Systemd Service (Recommended)

For production environments, run the Pi Agent as a system service to ensure it starts automatically on boot and recovers from failures.

Create `/etc/systemd/system/pi-agent.service`:

```ini
[Unit]
Description=Pi Agent Service
After=network.target

[Service]
ExecStart=/path/to/your/pi-agent/venv/bin/python /path/to/your/pi-agent/main.py
WorkingDirectory=/path/to/your/pi-agent
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi
Group=pi
EnvironmentFile=/path/to/your/pi-agent/.env

[Install]
WantedBy=multi-user.target
```

**Replace `/path/to/your/pi-agent/` with the actual path to your cloned repository.**

```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-agent.service
sudo systemctl start pi-agent.service
sudo systemctl status pi-agent.service
```

---

## 📦 End-to-End Deployment Guide (New Device)

This section walks through turning a **fresh Raspberry Pi** into a fully working camera agent that auto-starts and uploads recordings.

**Assumptions:** Raspberry Pi OS installed, internet access, camera connected.

### Step 1 — Flash & Boot

Flash Raspberry Pi OS Lite (recommended), then SSH in:

```bash
ssh pi@<ip-address>
```

### Step 2 — Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 3 — Install Required Packages

```bash
sudo apt install -y \
  python3 python3-pip python3-venv \
  ffmpeg \
  rpicam-apps \
  libcamera-dev \
  git
```

### Step 4 — Enable Camera

```bash
sudo raspi-config
# Navigate: Interface Options → Camera → Enable
sudo reboot
```

### Step 5 — Create Storage Directory

```bash
mkdir -p /home/pi/videos
```

### Step 6 — Copy Agent Code

**Option A (Recommended): Clone from Git**
```bash
cd /home/pi
git clone https://your-repo-url/pi-agent.git
cd pi-agent
```

**Option B: Copy from master Pi**
```bash
scp -r pi@PI001_IP:/home/pi/pi-agent /home/pi/
```

### Step 7 — Configure Device Identity

```bash
nano config.py
```

Change per device:
```python
DEVICE_ID   = "pi-002"
DEVICE_NAME = "Court Camera 2"
S3_PREFIX   = "videos/pi-002/"

# AWS credentials
AWS_ACCESS_KEY = ""
AWS_SECRET_KEY = ""
AWS_REGION     = ""
AWS_BUCKET     = ""
```

> ⚠️ Ensure your S3 bucket permissions allow uploads.

### Step 8 — Install Python Dependencies

```bash
cd ~/pi-agent
python3 -m venv venv
source venv/bin/activate
pip install boto3 paho-mqtt
```

### Step 9 — Test Camera

```bash
rpicam-vid -t 3000 -o test.h264
```

If this fails → check hardware connection or camera config.

### Step 10 — Run Agent Manually (Test)

```bash
venv/bin/python main.py
```

Expected output:
```
[Agent] Starting for device: pi-002
[MQTT] Connected
```

### Step 11 — Test Recording Remotely via MQTT

Publish a START command to topic `pi/pi-002/command`:
```json
{"command": "start_recording", "recordingId": "test1"}
```

Then publish a STOP command:
```json
{"command": "stop_recording"}
```

Verify that:
- ✔ Video is saved
- ✔ Upload is triggered
- ✔ File is removed after upload
- ✔ S3 URL is returned

### Step 12 — Enable Auto-Start (Systemd)

```bash
sudo nano /etc/systemd/system/pi-agent.service
```

```ini
[Unit]
Description=Pi Camera Agent
After=network-online.target
Wants=network-online.target

[Service]
User=pi
WorkingDirectory=/home/pi/pi-agent
ExecStart=/home/pi/pi-agent/venv/bin/python /home/pi/pi-agent/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-agent
sudo systemctl start pi-agent
systemctl status pi-agent
```

Monitor logs:
```bash
journalctl -u pi-agent -f
```

### Step 13 — Reboot Test

```bash
sudo reboot
# After boot:
systemctl status pi-agent  # must be running automatically
```

### Step 14 — Create a Master Image (for Scaling)

Once one Pi is working perfectly, clone its SD card for fast scaling:

```bash
sudo dd if=/dev/sdX of=pi-agent.img bs=4M status=progress
```

Flash this image to new cards, then only change `DEVICE_ID` and `DEVICE_NAME` per device.

### Step 15 — Auto Provisioning Script

For faster setup on new devices, use a `setup.sh` script:

```bash
#!/bin/bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv ffmpeg rpicam-apps git
mkdir -p /home/pi/videos
cd /home/pi
git clone https://repo/pi-agent.git
cd pi-agent
python3 -m venv venv
source venv/bin/activate
pip install boto3 paho-mqtt
sudo systemctl enable pi-agent
```

```bash
bash setup.sh
```

### Multi-Device Deployment Strategy

| Scale | Strategy |
|---|---|
| 5–10 devices | Clone SD image, change device ID |
| 50+ devices | `git pull` updates + provisioning script + Ansible |
| Large scale | Device provisioning server + OTA updates + central monitoring |

### ⚠️ Common Deployment Failures

| Issue | Solution |
|---|---|
| Camera not detected / `libcamera` error | Enable camera in `raspi-config`, check ribbon cable |
| Upload fails | Verify AWS keys and bucket policy |
| No MQTT connection | Check firewall settings and broker IP |
| Service not starting | Run `journalctl -u pi-agent -f` to inspect logs |

---

## 🤝 Contributing

1. **Fork** the repository.
2. **Create a new branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**.
4. **Commit**: `git commit -m 'feat: Add new feature'`
5. **Push**: `git push origin feature/your-feature-name`
6. **Open a Pull Request**.

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **Requests**: For simplifying HTTP requests.
- **picamera**: For robust camera interface on Raspberry Pi.
- **RPi.GPIO**: For GPIO interaction.
- **python-dotenv**: For convenient environment variable management.
- **schedule**: For easy in-process scheduling of tasks.
- **boto3**: For AWS S3 integration.
- **paho-mqtt**: For MQTT communication.

## 📞 Support & Contact

- 🐛 Issues: [GitHub Issues](https://github.com/T-Rajeev30/pi-agent/issues)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by [T-Rajeev30](https://github.com/T-Rajeev30)

</div>
