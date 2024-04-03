import os
import sys
import json
import time
import asyncio
import logging

from dotenv import load_dotenv, find_dotenv

from aiocoap import Message, Context, POST
from aiocoap.error import NetworkError

from utils import (
    sys_exc,
    round_temp,
    get_delta_temp,
    generate_payload,
    get_next_interval,
    set_logging_handler,
    generate_serial_number,
)


async def main():
    # Load env variables
    load_dotenv(find_dotenv())
    COAP_HOST = os.environ["COAP_HOST"]
    COAP_PORT = int(os.environ["COAP_PORT"])
    COAP_PATH = os.environ["COAP_PATH"]
    COAP_DEVICES = min(25, int(os.environ["COAP_DEVICES"]))
    COAP_MIN_ITERVAL_MS = int(os.environ["COAP_MIN_ITERVAL_MS"])
    COAP_MAX_ITERVAL_MS = int(os.environ["HTTP_MAX_ITERVAL_MS"])
    COAP_URI = f"coap://{COAP_HOST}:{COAP_PORT}/{COAP_PATH}"

    SEED = "coap"
    MANUFACTURER = "CoAP"
    DEVICE_FAMILY = "CPd"

    # Devices cache
    devices = dict()
    for _id in range(COAP_DEVICES):
        serial_number = generate_serial_number(_id, SEED)
        devices[_id] = {
            "serial_number": serial_number,
            "temperature": get_delta_temp(25, 5),
            "last_sent": get_next_interval(COAP_MIN_ITERVAL_MS, COAP_MAX_ITERVAL_MS),
            "location": f"Region_{int(serial_number, 16) % 100:02d}",
        }

    client = await Context.create_client_context()

    try:
        message = None
        while True:
            for _id in range(COAP_DEVICES):
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
                            temperature_key="tmp",
                            manufacturer_key="manufacturer",
                            dev_family_key="family",
                            location_key="pos",
                            serial_number_key="sn",
                        )
                        request = Message(
                            code=POST,
                            payload=json.dumps(message).encode("utf-8"),
                            uri=COAP_URI,
                        )
                        response = await client.request(request).response
                        logging.info(f"Result ({response.code}): {response.payload}")
                        devices[_id]["last_sent"] = get_next_interval(
                            COAP_MIN_ITERVAL_MS,
                            COAP_MAX_ITERVAL_MS,
                        )
                        logging.info(
                            f"Sent message from device ({devices[_id]['serial_number']}) to URI {COAP_URI}: {message}"
                        )

                except (Exception, NetworkError) as err:
                    logging.error(sys_exc(sys.exc_info()))
                    logging.error(
                        f"Error when sending message from device ({devices[_id]['serial_number']}) to URI {COAP_URI}: {message}"
                    )
                    if err.__class__ == NetworkError:
                        client = await Context.create_client_context()
                        await asyncio.sleep(1)

            await asyncio.sleep(0.05)

    except KeyboardInterrupt:
        logging.info("CTRL-C pressed by user")


if __name__ == "__main__":

    FILE_APP = os.path.splitext(os.path.split(__file__)[-1])[0]
    set_logging_handler(FILE_APP)

    # Load env variables
    load_dotenv(find_dotenv())

    asyncio.run(main())
