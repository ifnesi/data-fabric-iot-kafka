import os
import sys
import time
import logging

from dotenv import load_dotenv, find_dotenv
from configparser import ConfigParser

from confluent_kafka import Producer
from confluent_kafka.serialization import (
    StringSerializer,
    SerializationContext,
    MessageField,
)
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

from utils import (
    sys_exc,
    round_temp,
    get_delta_temp,
    generate_payload,
    get_next_interval,
    set_logging_handler,
    get_details,
)


def delivery_report(
    err,
    msg,
) -> None:
    if isinstance(msg.key(), bytes):
        key = msg.key().decode("utf-8")
    else:
        key = msg.key()
    if err is not None:
        logging.error(
            f"Delivery failed for record/key '{key}' for the topic '{msg.topic()}': {err}"
        )
    else:
        logging.info(
            f"Record/key '{key}' successfully produced to topic/partition '{msg.topic()}/{msg.partition()}' at offset #{msg.offset()}"
        )


if __name__ == "__main__":

    FILE_APP = os.path.splitext(os.path.split(__file__)[-1])[0]
    set_logging_handler(FILE_APP)

    # Load env variables
    load_dotenv(find_dotenv())
    KAFKA_CONFIG_FILE = os.environ["KAFKA_CONFIG_FILE"]
    KAFKA_CLIENT_ID = os.environ["KAFKA_CLIENT_ID"]
    KAFKA_TOPIC = os.environ["KAFKA_TOPIC"]
    KAFKA_MIN_ITERVAL_MS = int(os.environ["KAFKA_MIN_ITERVAL_MS"])
    KAFKA_MAX_ITERVAL_MS = int(os.environ["KAFKA_MAX_ITERVAL_MS"])
    KAFKA_SCHEMA_FILE = os.environ["KAFKA_SCHEMA_FILE"]
    KAFKA_DEVICES = min(25, int(os.environ["KAFKA_DEVICES"]))

    SEED = "kafka"
    MANUFACTURER = "KafkaTemp"
    DEVICE_FAMILY = "K1"

    # Devices cache
    devices = dict()
    for _id in range(KAFKA_DEVICES):
        serial_number, location, temp_mu, temp_sigma = get_details(_id, SEED)
        devices[_id] = {
            "serial_number": serial_number,
            "temperature": get_delta_temp(temp_mu, temp_sigma),
            "last_sent": get_next_interval(KAFKA_MIN_ITERVAL_MS, KAFKA_MAX_ITERVAL_MS),
            "location": location,
        }

    config = ConfigParser()
    config.read(KAFKA_CONFIG_FILE)

    # Producer
    kafka_config = dict(config["kafka"])
    kafka_config.update(
        {
            "client.id": KAFKA_CLIENT_ID,
        }
    )
    producer = Producer(kafka_config)

    # Schema Registry
    schema_registry_config = dict(config["schema-registry"])
    schema_registry_client = SchemaRegistryClient(schema_registry_config)
    with open(KAFKA_SCHEMA_FILE, "r") as f:
        schema_str = f.read()
    avro_serializer = AvroSerializer(
        schema_registry_client,
        schema_str=schema_str,
    )
    string_serializer = StringSerializer("utf_8")

    # Main thread loop
    try:
        while True:
            for _id in range(KAFKA_DEVICES):
                try:
                    if devices[_id]["last_sent"] < time.time():
                        devices[_id]["temperature"] = round_temp(
                            devices[_id]["temperature"] + get_delta_temp()
                        )
                        producer.poll(0)
                        value = generate_payload(
                            devices[_id]["temperature"],
                            serial_number=devices[_id]["serial_number"],
                            manufacturer=MANUFACTURER,
                            dev_family=DEVICE_FAMILY,
                            location=devices[_id]["location"],
                            temperature_key="temperature",
                            manufacturer_key="manufacturer",
                            dev_family_key="product",
                            location_key="region",
                            timestamp_key="datetime",
                            serial_number_key="id",
                            _timestamp_epoch=False,
                        )

                        producer.produce(
                            topic=KAFKA_TOPIC,
                            key=string_serializer(devices[_id]["serial_number"]),
                            value=avro_serializer(
                                value,
                                SerializationContext(
                                    KAFKA_TOPIC,
                                    MessageField.VALUE,
                                ),
                            ),
                            on_delivery=delivery_report,
                        )

                        devices[_id]["last_sent"] = get_next_interval(
                            KAFKA_MIN_ITERVAL_MS,
                            KAFKA_MAX_ITERVAL_MS,
                        )

                except Exception:
                    logging.error(sys_exc(sys.exc_info()))

            time.sleep(0.05)

    except KeyboardInterrupt:
        logging.info("CTRL-C pressed by user")

    finally:
        logging.info("Flushing Kafka Producer")
        producer.flush()
