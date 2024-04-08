import os
import sys
import json
import pika
import time
import logging

from dotenv import load_dotenv, find_dotenv

from utils import (
    sys_exc,
    round_temp,
    get_delta,
    generate_payload,
    get_next_interval,
    set_logging_handler,
    get_details,
)


def connect(
    host: str,
    port: int,
    channel: str,
) -> tuple:
    _connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=host,
            port=port,
        )
    )
    _channel = _connection.channel()
    _channel.queue_declare(queue=channel)
    return (
        _connection,
        _channel,
    )


if __name__ == "__main__":

    FILE_APP = os.path.splitext(os.path.split(__file__)[-1])[0]
    set_logging_handler(FILE_APP)

    # Load env variables
    load_dotenv(find_dotenv())
    LOCATION_DATA = os.environ["LOCATION_DATA"]
    RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
    RABBITMQ_PORT = int(os.environ["RABBITMQ_PORT"])
    RABBITMQ_DEVICES = min(25, int(os.environ["RABBITMQ_DEVICES"]))
    RABBITMQ_QUEUE = os.environ["RABBITMQ_QUEUE"]
    RABBITMQ_MIN_ITERVAL_MS = int(os.environ["RABBITMQ_MIN_ITERVAL_MS"])
    RABBITMQ_MAX_ITERVAL_MS = int(os.environ["RABBITMQ_MAX_ITERVAL_MS"])

    SEED = "$Rabbitmq"
    MANUFACTURER = "RMQ"
    DEVICE_FAMILY = "sx"

    # Devices cache
    devices = dict()
    for _id in range(RABBITMQ_DEVICES):
        serial_number, location, temp_mu, temp_sigma = get_details(
            _id,
            SEED,
            LOCATION_DATA,
        )
        devices[_id] = {
            "serial_number": serial_number,
            "temperature": get_delta(temp_mu, temp_sigma),
            "last_sent": get_next_interval(
                RABBITMQ_MIN_ITERVAL_MS,
                RABBITMQ_MAX_ITERVAL_MS,
            ),
            "location": location,
        }

    # RabbitMQ Connection/Channel
    connection, channel = connect(
        RABBITMQ_HOST,
        RABBITMQ_PORT,
        RABBITMQ_QUEUE,
    )

    # Main thread loop
    try:
        while True:
            if channel is not None and channel.is_open:
                for _id in range(RABBITMQ_DEVICES):
                    try:
                        if devices[_id]["last_sent"] < time.time():
                            devices[_id]["temperature"] = round_temp(
                                devices[_id]["temperature"] + get_delta()
                            )
                            message = generate_payload(
                                devices[_id]["temperature"],
                                serial_number=devices[_id]["serial_number"],
                                manufacturer=MANUFACTURER,
                                dev_family=DEVICE_FAMILY,
                                location=devices[_id]["location"]["city"],
                                lat=devices[_id]["location"]["lat"],
                                lng=devices[_id]["location"]["lng"],
                                location_key="region",
                                lat_key="lat",
                                lng_key="lon",
                                temperature_key="temp",
                                manufacturer_key="provider",
                                dev_family_key="product",
                                serial_number_key="serno",
                                _timestamp_epoch=False,
                            )
                            channel.basic_publish(
                                exchange="",
                                routing_key=RABBITMQ_QUEUE,
                                body=json.dumps(message),
                            )
                            devices[_id]["last_sent"] = get_next_interval(
                                RABBITMQ_MIN_ITERVAL_MS,
                                RABBITMQ_MAX_ITERVAL_MS,
                            )
                            logging.info(
                                f"Sent message from device ({devices[_id]['serial_number']}) to queue {RABBITMQ_QUEUE}: {message}"
                            )
                    except Exception:
                        logging.error(sys_exc(sys.exc_info()))
                        logging.error(
                            f"Error when sending message from device ({devices[_id]['serial_number']}) to queue {RABBITMQ_QUEUE}: {message}"
                        )

            else:
                connection, channel = connect(
                    RABBITMQ_HOST,
                    RABBITMQ_PORT,
                    RABBITMQ_QUEUE,
                )

            time.sleep(0.05)

    except KeyboardInterrupt:
        logging.info("CTRL-C pressed by user")

    finally:
        logging.info("Closing channel/connection")
        if channel is not None:
            try:
                channel.close()
            except Exception:
                logging.error(sys_exc(sys.exc_info()))
        if connection is not None:
            try:
                connection.close()
            except Exception:
                logging.error(sys_exc(sys.exc_info()))
