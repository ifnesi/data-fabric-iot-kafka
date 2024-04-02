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
    get_delta_temp,
    generate_payload,
    get_next_interval,
    set_logging_handler,
    generate_serial_number,
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
    RABBITMQ_HOST = os.environ["RABBITMQ_HOST"]
    RABBITMQ_PORT = int(os.environ["RABBITMQ_PORT"])
    RABBITMQ_DEVICES = min(25, int(os.environ["RABBITMQ_DEVICES"]))
    RABBITMQ_CHANNEL = os.environ["RABBITMQ_CHANNEL"]
    RABBITMQ_MIN_ITERVAL_MS = int(os.environ["RABBITMQ_MIN_ITERVAL_MS"])
    RABBITMQ_MAX_ITERVAL_MS = int(os.environ["RABBITMQ_MAX_ITERVAL_MS"])

    SEED = "rabbitmq"
    MANUFACTURER = "RMQ"
    DEVICE_FAMILY = "sx"

    # Devices cache
    devices = dict()
    for _id in range(RABBITMQ_DEVICES):
        serial_number = generate_serial_number(_id, SEED)
        devices[_id] = {
            "serial_number": serial_number,
            "temperature": get_delta_temp(25, 5),
            "last_sent": get_next_interval(
                RABBITMQ_MIN_ITERVAL_MS,
                RABBITMQ_MAX_ITERVAL_MS,
            ),
            "location": f"Region_{int(serial_number, 16) % 100:02d}",
        }

    # RabbitMQ Connection/Channel
    connection, channel = connect(
        RABBITMQ_HOST,
        RABBITMQ_PORT,
        RABBITMQ_CHANNEL,
    )

    # Main thread loop
    try:
        while True:
            if channel is not None and channel.is_open:
                for _id in range(RABBITMQ_DEVICES):
                    try:
                        if devices[_id]["last_sent"] < time.time():
                            devices[_id]["temperature"] = round_temp(
                                devices[_id]["temperature"] + get_delta_temp()
                            )
                            message = generate_payload(
                                devices[_id]["temperature"],
                                serial_number=devices[_id]["serial_number"],
                                manufacturer=MANUFACTURER,
                                dev_family=DEVICE_FAMILY,
                                location=devices[_id]["location"],
                                temperature_key="temp",
                                manufacturer_key="provider",
                                dev_family_key="product",
                                location_key="region",
                                serial_number_key="serno",
                            )
                            channel.basic_publish(
                                exchange="",
                                routing_key=RABBITMQ_CHANNEL,
                                body=json.dumps(message),
                            )
                            devices[_id]["last_sent"] = get_next_interval(
                                RABBITMQ_MIN_ITERVAL_MS,
                                RABBITMQ_MAX_ITERVAL_MS,
                            )
                            logging.info(
                                f"Sent message from device ({devices[_id]['serial_number']}) to queue {RABBITMQ_CHANNEL}: {message}"
                            )
                    except Exception:
                        logging.error(sys_exc(sys.exc_info()))
                        logging.error(
                            f"Error when sending message from device ({devices[_id]['serial_number']}) to queue {RABBITMQ_CHANNEL}: {message}"
                        )

            else:
                connection, channel = connect(
                    RABBITMQ_HOST,
                    RABBITMQ_PORT,
                    RABBITMQ_CHANNEL,
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
