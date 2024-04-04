import os
import sys
import time
import logging
import requests

from dotenv import load_dotenv, find_dotenv

from utils import (
    sys_exc,
    round_temp,
    get_delta_temp,
    generate_payload,
    get_next_interval,
    set_logging_handler,
    get_details,
)


class HTTPRestProxyClient:
    def __init__(
        self,
        base_url: str,
    ) -> None:
        self.base_url = base_url

    def _submit(
        self,
        path: str,
        verb: str = "GET",
        headers: dict = None,
        body: dict = None,
    ):
        if verb == "POST":
            session = requests.post
        elif verb == "PATCH":
            session = requests.patch
        elif verb == "PUT":
            session = requests.put
        elif verb == "DELETE":
            session = requests.delete
        else:
            session = requests.get

        try:
            response = session(
                path,
                headers=headers,
                json=body,
            )
        except Exception:
            status_code = 500
            response = sys_exc(sys.exc_info())
            logging.error(response)
        else:
            status_code = response.status_code
            response = response.json()

        return status_code, response

    def produce_json(
        self,
        topic_name: str,
        key: str,
        value: dict,
    ) -> None:
        headers = {
            "Content-Type": "application/vnd.kafka.json.v2+json",
            "Accept": "application/vnd.kafka.v2+json, application/vnd.kafka+json, application/json",
        }
        status_code, response = self._submit(
            f"{self.base_url}/topics/{topic_name}",
            verb="POST",
            headers=headers,
            body={
                "records": [
                    {
                        "key": key,
                        "value": value,
                    }
                ]
            },
        )
        if status_code == 200:
            logging.info(f"Message produced to topic {topic_name}: {key} | {value}")
        else:
            logging.error(
                f"Unable to produce message to topic {topic_name}: {key} | {value} ({status_code | {response}})"
            )


if __name__ == "__main__":

    FILE_APP = os.path.splitext(os.path.split(__file__)[-1])[0]
    set_logging_handler(FILE_APP)

    # Load env variables
    load_dotenv(find_dotenv())
    HTTP_SCHEME = os.environ["HTTP_SCHEME"]
    HTTP_HOST = os.environ["HTTP_HOST"]
    HTTP_PORT = int(os.environ["HTTP_PORT"])
    KAFKA_HTTP_CLIENT_ID = os.environ["KAFKA_HTTP_CLIENT_ID"]
    KAFKA_HTTP_TOPIC = os.environ["KAFKA_HTTP_TOPIC"]
    KAFKA_SCHEMA_FILE = os.environ["KAFKA_SCHEMA_FILE"]
    HTTP_DEVICES = min(25, int(os.environ["HTTP_DEVICES"]))
    HTTP_MIN_ITERVAL_MS = int(os.environ["HTTP_MIN_ITERVAL_MS"])
    HTTP_MAX_ITERVAL_MS = int(os.environ["HTTP_MAX_ITERVAL_MS"])

    SEED = "http"
    MANUFACTURER = "KafkaHttpTemp"
    DEVICE_FAMILY = "Kh1"

    # Devices cache
    devices = dict()
    for _id in range(HTTP_DEVICES):
        serial_number, location, temp_mu, temp_sigma = get_details(_id, SEED)
        devices[_id] = {
            "serial_number": serial_number,
            "temperature": get_delta_temp(temp_mu, temp_sigma),
            "last_sent": get_next_interval(HTTP_MIN_ITERVAL_MS, HTTP_MAX_ITERVAL_MS),
            "location": location,
        }

    client = HTTPRestProxyClient(f"{HTTP_SCHEME}://{HTTP_HOST}:{HTTP_PORT}")

    # Main thread loop
    try:
        while True:
            for _id in range(HTTP_DEVICES):
                try:
                    if devices[_id]["last_sent"] < time.time():
                        devices[_id]["temperature"] = round_temp(
                            devices[_id]["temperature"] + get_delta_temp()
                        )
                        value = generate_payload(
                            devices[_id]["temperature"],
                            serial_number=devices[_id]["serial_number"],
                            manufacturer=MANUFACTURER,
                            dev_family=DEVICE_FAMILY,
                            location=devices[_id]["location"],
                            temperature_key="temp",
                            manufacturer_key="mnf",
                            dev_family_key="prd",
                            location_key="loc",
                            timestamp_key="tm",
                            serial_number_key="sn",
                        )
                        client.produce_json(
                            KAFKA_HTTP_TOPIC,
                            devices[_id]["serial_number"],
                            value,
                        )
                        devices[_id]["last_sent"] = get_next_interval(
                            HTTP_MIN_ITERVAL_MS,
                            HTTP_MAX_ITERVAL_MS,
                        )

                except Exception:
                    logging.error(sys_exc(sys.exc_info()))

            time.sleep(0.05)

    except KeyboardInterrupt:
        logging.info("CTRL-C pressed by user")

    finally:
        logging.info("Stopped HTTP client")
