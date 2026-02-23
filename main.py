import json, logging, os, signal, sys, threading, time
import paho.mqtt.client as mqtt
import recorder
from config import DEVICE_ID, DEVICE_NAME, HEARTBEAT_INTERVAL, MQTT_BROKER, MQTT_KEEPALIVE, MQTT_PORT

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

_mqtt_client = None
_heartbeat_failures = 0
_MAX_HB_FAILURES = 3

def on_connect(client, userdata, flags, rc):
    global _heartbeat_failures
    if rc == 0:
        _heartbeat_failures = 0
        log.info(f"[MQTT] Connected to {MQTT_BROKER}")
        client.subscribe(f"pi/{DEVICE_ID}/command", qos=1)
    else:
        log.error(f"[MQTT] Connection failed rc={rc}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        log.warning(f"[MQTT] Disconnected rc={rc}, reconnecting...")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        command = data.get("command", "")
        log.info(f"[MQTT] Command: {command}")
        if command == "start_recording":
            if recorder.is_recording():
                return
            recording_id = data.get("recordingId")
            if not recording_id:
                log.error("[MQTT] Missing recordingId")
                return
            recorder.start_recording(client, recording_id)
        elif command == "stop_recording":
            if recorder.is_recording():
                recorder.stop_recording(client)
    except Exception as e:
        log.exception(f"[MQTT] Error: {e}")

def heartbeat_loop(client):
    global _heartbeat_failures
    while True:
        time.sleep(HEARTBEAT_INTERVAL)
        try:
            status = "recording" if recorder.is_recording() else "standby"
            payload = json.dumps({"deviceId": DEVICE_ID, "name": DEVICE_NAME, "status": status})
            result = client.publish(f"pi/{DEVICE_ID}/heartbeat", payload, qos=0)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                _heartbeat_failures = 0
            else:
                _heartbeat_failures += 1
        except Exception as e:
            _heartbeat_failures += 1
            log.error(f"[Heartbeat] Error: {e}")
        if _heartbeat_failures >= _MAX_HB_FAILURES:
            log.error("[Heartbeat] Too many failures, reconnecting")
            _heartbeat_failures = 0
            try:
                client.reconnect()
            except Exception as e:
                log.error(f"[Heartbeat] Reconnect error: {e}")

def shutdown(signum, frame):
    log.info("[Agent] Shutting down")
    if recorder.is_recording():
        recorder.stop_recording(_mqtt_client)
        time.sleep(2)
    if _mqtt_client:
        _mqtt_client.disconnect()
    sys.exit(0)

def main():
    global _mqtt_client
    log.info(f"[Agent] Starting for device: {DEVICE_ID}")
    client = mqtt.Client(client_id=f"pi-agent-{DEVICE_ID}", clean_session=False, protocol=mqtt.MQTTv311)
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
    client.loop_forever(retry_first_connection=True)

if __name__ == "__main__":
    main()

