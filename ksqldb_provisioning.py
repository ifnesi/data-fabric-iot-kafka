import os
import re
import glob
import json
import time
import logging
import requests

from dotenv import load_dotenv, find_dotenv

from utils import set_logging_handler


def flat_file(file: str) -> str:
    with open(file, "r") as f:
        data = " ".join([line.strip("\n").strip(" ") for line in f.readlines()])
    return data


def repl_env_vars(text: str) -> str:
    env_vars = set(re.findall("\$([A-Za-z-_]+)", text))
    for var in env_vars:
        if var in os.environ.keys():
            text = text.replace(f"${var}", os.environ[var])
    return text


if __name__ == "__main__":
    FILE_APP = os.path.splitext(os.path.split(__file__)[-1])[0]
    set_logging_handler(FILE_APP)

    # Load env variables
    load_dotenv(find_dotenv())

    logging.info("Submitting ksqlDB statements\n")
    for file in sorted(glob.glob(os.path.join("ksqldb", "*.sql"))):
        statement = repl_env_vars(flat_file(file))
        logging.info(f"{file}:\n{statement}")
        try:
            response = requests.post(
                "http://localhost:8088/ksql",
                headers={
                    "Content-Type": "application/vnd.ksql.v1+json; charset=utf-8",
                },
                json={
                    "ksql": statement,
                    "streamsProperties": {
                        "ksql.streams.auto.offset.reset": "earliest",
                        "ksql.streams.cache.max.bytes.buffering": "0",
                    },
                },
            )

            if response.status_code == 200:
                log = logging.info
                status_code = response.status_code
                response = json.dumps(response.json(), indent=3)
            else:
                log = logging.error
                status_code = response.status_code
                response = json.dumps(response.json(), indent=3)

        except Exception as err:
            log = logging.critical
            status_code = "50X"
            response = err

        finally:
            log(f"Response [Status Code = {status_code}]:\n{response}\n")

        time.sleep(5)
