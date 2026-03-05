import json
import os
import tempfile

STATE_FILE = "/home/pi/pi-agent/recording_state.json"


def save_state(data: dict):
    dir_ = os.path.dirname(STATE_FILE)
    os.makedirs(dir_, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False) as tf:
        json.dump(data, tf)
        tmp_path = tf.name

    os.replace(tmp_path, STATE_FILE)


def load_state():
    if not os.path.exists(STATE_FILE):
        return None

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None


def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
