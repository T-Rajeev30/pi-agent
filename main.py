import json
import logging
import os
import signal
import sys
import threading
import time

import paho.mqtt.client as mqtt

import recorder
from storage_manager import StorageManager
from config_manager import ConfigManager
from monitoring_manager import MonitoringManager
from uploader import upload_file
from upload_queue import start_retry_worker
from recovery import recover_pending_files

from config import (
    DEVICE_ID,
    DEVICE_NAME,
    COURT_FIELD,
    HEARTBEAT_INTERVAL,
    MQTT_BROKER,
    MQTT_KEEPALIVE,
    MQTT_PORT,
)

# -------------------------------------------------- #
# LOGGING
# -------------------------------------------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

log = logging.getLogger("pi-agent")

_mqtt_client = None
_shutdown_event = threading.Event()


# -------------------------------------------------- #
# MQTT CALLBACKS
# -------------------------------------------------- #

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        log.info(f"[MQTT] Connected → {MQTT_BROKER}")
        client.subscribe(f"pi/{DEVICE_ID}/command", qos=1)
    else:
        log.error(f"[MQTT] Connection failed rc={reason_code}")


def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        log.warning("[MQTT] Unexpected disconnect. Auto-reconnect active.")


def on_message(client, userdata, msg):
    try:
        if msg.retain:
            log.warning("[MQTT] Ignoring retained command")
            return

        payload = json.loads(msg.payload.decode())
        command = payload.get("command")

        log.info(f"[MQTT] Command received → {command}")

        if command == "start_recording":
            handle_start_recording(client, payload)

        elif command == "stop_recording":
            handle_stop_recording(client)

        else:
            log.warning(f"[MQTT] Unknown command: {command}")

    except Exception as e:
        log.exception(f"[MQTT] Processing error: {e}")


# -------------------------------------------------- #
# COMMAND HANDLERS
# -------------------------------------------------- #

def handle_start_recording(client, payload):
    if recorder.is_recording():
        log.warning("[Recorder] Already recording")
        return

    recording_id = payload.get("recordingId")
    duration = payload.get("duration", 3600)  # Default to 1 hour if not provided

    if not recording_id:
        log.error("[Recorder] Missing recordingId")
        return

    recorder.start_recording(client, recording_id, duration)


def handle_stop_recording(client):
    if recorder.is_recording():
        recorder.stop_recording(client, manual_stop=True)
    else:
        log.warning("[Recorder] Stop ignored — not recording")


# -------------------------------------------------- #
# HEARTBEAT
# -------------------------------------------------- #

def heartbeat_loop(client):
    while not _shutdown_event.is_set():
        try:
            status = recorder.get_status()
            remaining_time = recorder.get_remaining_time()

            payload = json.dumps({
                "deviceId": DEVICE_ID,
                "deviceName": DEVICE_NAME,
                "court": COURT_FIELD,
                "status": status,
                "remainingTime": remaining_time,
            })

            client.publish(
                f"pi/{DEVICE_ID}/heartbeat",
                payload,
                retain=True,
            )

        except Exception as e:
            log.error(f"[Heartbeat] Error: {e}")

        _shutdown_event.wait(HEARTBEAT_INTERVAL)


# -------------------------------------------------- #
# SHUTDOWN
# -------------------------------------------------- #

def shutdown(signum, frame):
    log.info("[Agent] Shutdown initiated")
    _shutdown_event.set()

    try:
        if recorder.is_recording():
            log.info("[Recorder] Stopping active recording before exit")
            recorder.stop_recording(_mqtt_client, manual_stop=True)
            time.sleep(2)

        if _mqtt_client:
            _mqtt_client.loop_stop()
            _mqtt_client.disconnect()

    finally:
        os._exit(0)


# -------------------------------------------------- #
# MQTT CLIENT FACTORY
# -------------------------------------------------- #

def create_mqtt_client():
    client = mqtt.Client(
        client_id=f"pi-agent-{DEVICE_ID}",
        clean_session=False,
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.reconnect_delay_set(min_delay=1, max_delay=30)

    return client


# -------------------------------------------------- #
# MAIN
# -------------------------------------------------- #

def main():
    global _mqtt_client

    log.info(f"[Agent] Starting → Device: {DEVICE_ID}")

    # 1️⃣ Load configuration
    config_manager = ConfigManager()
    config_manager.load_config()

    # 2️⃣ Initialize storage manager
    storage_manager = StorageManager(config_manager)

    # 3️⃣ Initialize monitoring manager
    monitoring_manager = MonitoringManager(config_manager)

    # 4️⃣ Create MQTT client
    client = create_mqtt_client()
    _mqtt_client = client

    # 5️⃣ Register signals
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    # 6️⃣ Connect MQTT
    try:
        client.connect_async(MQTT_BROKER, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
    except Exception as e:
        log.error(f"[MQTT] Initial connection failed: {e}")

    # 7️⃣ Start heartbeat thread
    threading.Thread(
        target=heartbeat_loop,
        args=(client,),
        daemon=True,
    ).start()

    # 8️⃣ Recover leftover files (watchdog logic)
    log.info("[Recovery] Checking pending recordings...")
    recover_pending_files(client)

    # 9️⃣ Start upload retry worker
    start_retry_worker(upload_file, client)

    # 🔟 Start monitoring
    monitoring_manager.start_monitoring()

    # 1️⃣1️⃣ Start MQTT loop
    client.loop_forever(retry_first_connection=True)


if __name__ == "__main__":
    main()
