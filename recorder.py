import subprocess
import os
import signal
from datetime import datetime
from config import VIDEO_DIR

os.makedirs(VIDEO_DIR, exist_ok=True)

proc = None
recording = False
start_time = None
raw_file = None


def pad(n): return str(n).zfill(2)

def format_date(d):
    return f"{pad(d.day)}_{pad(d.month)}_{d.year}"

def format_time(d):
    return f"{pad(d.hour)}-{pad(d.minute)}-{pad(d.second)}"


def start_recording():
    global proc, recording, start_time, raw_file

    if proc:
        raise Exception("Already recording")

    start_time = datetime.now()

    date_str = format_date(start_time)
    start_str = format_time(start_time)

    raw_file = f"{VIDEO_DIR}/GM_{date_str}_FROM_{start_str}.h264"

    print("Recording started:", raw_file)

    proc = subprocess.Popen([
        "rpicam-vid",
        "--codec", "h264",
        "--timeout", "0",
        "--width", "1280",
        "--height", "720",
        "--framerate", "60",
        "--bitrate", "6000000",
        "--profile", "high",
        "--level", "4.2",
        "--intra", "60",
        "--denoise", "off",
        "--inline",
        "--nopreview",
        "-o", raw_file
    ])

    recording = True
    return raw_file


def stop_recording():
    global proc, recording, start_time, raw_file

    if not proc:
        return None

    print("Stopping recording...")
    proc.send_signal(signal.SIGINT)
    proc.wait()

    recording = False
    proc = None

    end_time = datetime.now()

    date_str = format_date(start_time)
    start_str = format_time(start_time)
    end_str = format_time(end_time)

    final_raw = f"{VIDEO_DIR}/GM_{date_str}_FROM_{start_str}_TO_{end_str}.h264"
    os.rename(raw_file, final_raw)

    return final_raw


def is_recording():
    return recording
