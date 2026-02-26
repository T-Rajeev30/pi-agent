import os
import json
import logging
import signal
import sys
import threading
import time
import paho.mqtt.client as mqtt
import recorder
from uploader import upload_file
from upload_queue import start_retry_worker
from config import (
    DEVICE_ID,
    DEVICE_NAME,
    HEARTBEAT_INTERVAL,
    MQTT_BROKER,
    MQTT_KEEPALIVE,
    MQTT_PORT,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

_mqtt_client = None
_agent_start_time = time.time()

# ---------------- MQTT CALLBACKS ---------------- #
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        log.info(f"[MQTT] Connected to {MQTT_BROKER}")
        client.subscribe(f"pi/{DEVICE_ID}/command", qos=1)
    else:
        log.error(f"[MQTT] Connection failed rc={reason_code}")

def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code != 0:
        log.warning("[MQTT] Unexpected disconnect. Reconnecting...")

def on_message(client, userdata, msg):
    try:
        if msg.retain:
            log.warning(f"[MQTT] Ignoring retained message")
            return

        data = json.loads(msg.payload.decode())
        command = data.get("command", "")
        log.info(f"[MQTT] Command: {command}")

        if command == "start_recording":
            if recorder.is_recording():
                log.warning("[MQTT] Already recording, ignoring start")
                return
            recording_id = data.get("recordingId")
            if not recording_id:
                log.error("[MQTT] Missing recordingId")
                return
            recorder.start_recording(client, recording_id)

        elif command == "stop_recording":
            if recorder.is_recording():
                recorder.stop_recording(client)
            else:
                log.warning("[MQTT] Not recording, ignoring stop")

    except Exception as e:
        log.exception(f"[MQTT] Error: {e}")

# ---------------- HEARTBEAT ---------------- #
def heartbeat_loop(client):
    while True:
        try:
            status = "RECORDING" if recorder.is_recording() else "STANDBY"
            payload = json.dumps({
                "deviceId": DEVICE_ID,
                "name": DEVICE_NAME,
                "status": status
            })
            client.publish(
                f"pi/{DEVICE_ID}/heartbeat",
                payload,
                retain=True
            )
        except Exception as e:
            log.error(f"[Heartbeat] error: {e}")
        time.sleep(HEARTBEAT_INTERVAL)

# ---------------- SHUTDOWN ---------------- #
def shutdown(signum, frame):
    log.info("[Agent] Shutting down")
    if recorder.is_recording():
        recorder.stop_recording(_mqtt_client)
        time.sleep(2)
    if _mqtt_client:
        _mqtt_client.loop_stop()
        _mqtt_client.disconnect()
    os._exit(0)

# ---------------- MAIN ---------------- #
def main():
    global _mqtt_client

    log.info(f"[Agent] Starting for device: {DEVICE_ID}")

    client = mqtt.Client(
        client_id=f"pi-agent-{DEVICE_ID}",
        clean_session=True,
        protocol=mqtt.MQTTv311,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    _mqtt_client = client

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=MQTT_KEEPALIVE)
    except Exception as e:
        log.error(f"[Agent] Initial connect failed: {e}")

    threading.Thread(target=heartbeat_loop, args=(client,), daemon=True).start()
    start_retry_worker(upload_file, client)

    client.loop_forever(retry_first_connection=True)

if __name__ == "__main__":
    main()


