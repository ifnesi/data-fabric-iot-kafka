import os
import glob
import time
import logging
import requests

from utils import set_logging_handler


def flat_file(file: str) -> str:
    with open(file, "r") as f:
        data = " ".join([line.strip("\n").strip(" ") for line in f.readlines()])
    return data


if __name__ == "__main__":
    FILE_APP = os.path.splitext(os.path.split(__file__)[-1])[0]
    set_logging_handler(FILE_APP)

    logging.info("Submitting ksqlDB statements...")
    for file in sorted(glob.glob(os.path.join("ksqldb", "statement_*.sql"))):
        statement = flat_file(file)
        print("")
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
                response = response.json()
            else:
                log = logging.error
                status_code = response.status_code
                response = response.json()
        except Exception as err:
            log = logging.critical
            status_code = "50X"
            response = err
        finally:
            print("")
            log(f"Response [{status_code}]:\n{response}")

        time.sleep(3)
