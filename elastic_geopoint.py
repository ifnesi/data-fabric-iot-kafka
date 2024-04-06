import os
import time
import logging
import requests

from utils import set_logging_handler


if __name__ == "__main__":
    FILE_APP = os.path.splitext(os.path.split(__file__)[-1])[0]
    set_logging_handler(FILE_APP)

    BASE_URL = "http://localhost:9200"
    HEADERS = {
        "Content-Type": "application/json; charset=utf-8",
    }
    NEW_FIELD = "gps"
    SCRIPT = f"ctx._source.{NEW_FIELD}=[ctx._source.longitude,ctx._source.latitude];"

    logging.info(f"Creating Geo Point field on Elastic (Field Name: {NEW_FIELD})")

    # Get mappings
    logging.info("Get mappings")
    response = requests.get(f"{BASE_URL}/_mapping")
    mapping = list(response.json().keys())[0]
    logging.info(f"Status code: {response.status_code}. Mappings found: {mapping}")

    # Adding new field
    logging.info(f"Adding new field: {NEW_FIELD}")
    response = requests.put(
        f"{BASE_URL}/{mapping}/_mapping",
        headers=HEADERS,
        json={"properties": {"gps": {"type": "geo_point"}}},
    )
    logging.info(f"Status code: {response.status_code}")

    # Populating data
    while True:
        try:
            requests.post(
                f"{BASE_URL}/{mapping}/_update_by_query?wait_for_completion=true",
                headers=HEADERS,
                json={
                    "query": {
                        "match_all": {},
                    },
                    "script": {
                        "source": SCRIPT,
                        "lang": "painless",
                    },
                },
            )
        except Exception:
            pass
        finally:
            time.sleep(1)
