import time
import os
import socket
import paho.mqtt.client as mqtt

from config import DEVICE_ID, MQTT_BROKER, MQTT_PORT
from recorder import start_recording, stop_recording, is_recording
from converter import convert_to_mp4
from uploader import upload_large

raw_file = None


# =============================
# MQTT PUBLISH
# =============================
def publish(topic, msg, retain=False):
    try:
        client.publish(topic, msg, retain=retain)
    except Exception as e:
        print("Publish error:", e)


# =============================
# MQTT CALLBACKS
# =============================
def on_connect(client, userdata, flags, reasonCode, properties=None):
    print("Connected to MQTT →", reasonCode)

    client.subscribe(f"pi/{DEVICE_ID}/command")

    publish(f"pi/{DEVICE_ID}/status", "online", True)

    if is_recording():
        publish(f"pi/{DEVICE_ID}/recording", "ON", True)
    else:
        publish(f"pi/{DEVICE_ID}/recording", "OFF", True)


def on_message(client, userdata, msg):
    global raw_file

    command = msg.payload.decode().strip()
    print("CMD:", command)

    try:
        if command == "start_recording":

            if not is_recording():
                raw_file = start_recording()
                publish(f"pi/{DEVICE_ID}/recording", "ON", True)
            else:
                print("Already recording")

        elif command == "stop_recording":

            raw = stop_recording()
            publish(f"pi/{DEVICE_ID}/recording", "OFF", True)

            if raw:
                mp4 = convert_to_mp4(raw)
                url = upload_large(mp4)
                print("Uploaded:", url)

        elif command == "reboot":
            os.system("sudo reboot")

    except Exception as e:
        print("Command error:", e)


def on_disconnect(client, userdata, reasonCode, properties=None):
    print("MQTT disconnected")


# =============================
# MQTT CLIENT SETUP
# =============================
def create_client():
    client = mqtt.Client(
        protocol=mqtt.MQTTv311,   # prevents handshake stalls
        transport="tcp"
    )

    # Force IPv4 & prevent Bookworm IPv6 timeout
    client.socket_options = [(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)]

    return client


client = create_client()

client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

print("Connecting to broker...")

# IMPORTANT: use IP to avoid DNS/IPv6 issues
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=30)

client.loop_start()


# =============================
# HEARTBEAT LOOP
# =============================
try:
    while True:
        publish(f"pi/{DEVICE_ID}/heartbeat", "1")
        time.sleep(5)

except KeyboardInterrupt:
    print("Shutting down...")

    publish(f"pi/{DEVICE_ID}/status", "offline", True)

    client.loop_stop()

    try:
        client.disconnect()
    except:
        pass
