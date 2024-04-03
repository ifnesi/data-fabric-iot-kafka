import os
import sys
import json
import time
import logging

import paho.mqtt.client as mqtt

from dotenv import load_dotenv, find_dotenv

from utils import (
    sys_exc,
    round_temp,
    get_delta_temp,
    generate_payload,
    get_next_interval,
    set_logging_handler,
    generate_serial_number,
)


def connect_mqtt(
    host: str,
    port: int,
    client_id: str,
    keepalive: int,
):
    def on_log(
        client,
        userdata,
        level,
        message,
    ):
        logging.info(message)

    def on_connect(
        client,
        userdata,
        flags,
        rc,
        properties,
    ):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.error(f"Failed to connect, return code {rc}")

    def on_disconnect(
        client,
        userdata,
        flags,
        rc,
        properties,
    ):
        FIRST_RECONNECT_DELAY = 1
        RECONNECT_RATE = 2
        MAX_RECONNECT_COUNT = 12
        MAX_RECONNECT_DELAY = 5
        logging.info(f"Disconnected with result code: {rc}")
        reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
        while reconnect_count < MAX_RECONNECT_COUNT:
            logging.info(f"Reconnecting in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)

            try:
                client.reconnect()
                logging.info("Reconnected successfully!")
                return
            except Exception:
                logging.error(sys_exc(sys.exc_info()))

            reconnect_delay *= RECONNECT_RATE
            reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
            reconnect_count += 1
        logging.info(f"Reconnect failed after {reconnect_count} attempts. Exiting...")

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
    )
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_log = on_log
    client.connect(
        host,
        port=port,
        keepalive=keepalive,
    )
    return client


if __name__ == "__main__":

    FILE_APP = os.path.splitext(os.path.split(__file__)[-1])[0]
    set_logging_handler(FILE_APP)

    # Load env variables
    load_dotenv(find_dotenv())
    MQTT_HOST = os.environ["MQTT_HOST"]
    MQTT_PORT = int(os.environ["MQTT_PORT"])
    MQTT_KEEPALIVE = int(os.environ["MQTT_KEEPALIVE"])
    MQTT_CLIENT_ID = os.environ["MQTT_CLIENT_ID"]
    MQTT_DEVICES = min(25, int(os.environ["MQTT_DEVICES"]))
    MQTT_MIN_ITERVAL_MS = int(os.environ["MQTT_MIN_ITERVAL_MS"])
    MQTT_MAX_ITERVAL_MS = int(os.environ["MQTT_MAX_ITERVAL_MS"])

    SEED = "mqtt"
    MANUFACTURER = "PicoQ"
    DEVICE_FAMILY = "Q1"

    # Devices cache
    devices = dict()
    for _id in range(MQTT_DEVICES):
        serial_number = generate_serial_number(_id, SEED)
        devices[_id] = {
            "serial_number": serial_number,
            "temperature": round_temp(get_delta_temp(25, 5) * 9 / 5 + 32),
            "last_sent": get_next_interval(
                MQTT_MIN_ITERVAL_MS,
                MQTT_MAX_ITERVAL_MS,
            ),
            "location": f"Region_{int(serial_number, 16) % 100:02d}",
        }

    # Main thread loop
    client = connect_mqtt(
        MQTT_HOST,
        MQTT_PORT,
        MQTT_CLIENT_ID,
        MQTT_KEEPALIVE,
    )
    client.loop_start()
    try:
        while True:
            if client.is_connected:
                for _id in range(MQTT_DEVICES):
                    try:
                        if devices[_id]["last_sent"] < time.time():
                            devices[_id]["temperature"] = round_temp(
                                devices[_id]["temperature"] + get_delta_temp()
                            )
                            message = generate_payload(
                                devices[_id]["temperature"],
                                location=devices[_id]["location"],
                                temperature_key="temperature",
                                location_key="location",
                                timestamp_key="epoch",
                                unit="F",
                                _timestamp_epoch=False,
                            )
                            topic = f"python/mqtt/{MANUFACTURER}/{DEVICE_FAMILY}/{devices[_id]['serial_number']}"
                            result = client.publish(
                                topic,
                                json.dumps(message),
                            )
                            if result[0] == 0:
                                logging.info(
                                    f"Sent message from device ({devices[_id]['serial_number']}) to topic {topic}: {message}"
                                )
                            else:
                                logging.error(
                                    f"Error when sending message from device ({devices[_id]['serial_number']}) to topic {topic} (status={result[0]}): {message}"
                                )

                            devices[_id]["last_sent"] = get_next_interval(
                                MQTT_MIN_ITERVAL_MS,
                                MQTT_MAX_ITERVAL_MS,
                            )

                    except Exception:
                        logging.error(sys_exc(sys.exc_info()))
                        logging.error(
                            f"Error when sending message from device ({devices[_id]['serial_number']}) to topic {topic}: {message}"
                        )

            time.sleep(0.05)

    except KeyboardInterrupt:
        logging.info("CTRL-C pressed by user")

    finally:
        logging.info("Stopping MQTT loop")
        client.loop_stop()
