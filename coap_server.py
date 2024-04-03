import os
import json
import aiocoap
import asyncio
import logging

import aiocoap.resource as resource

from dotenv import load_dotenv, find_dotenv
from logging.handlers import TimedRotatingFileHandler

from utils import set_logging_handler


class TelemetryResource(resource.Resource):
    def __init__(
        self,
        logger,
        encoding: str = "utf-8",
    ):
        super().__init__()
        self.logger = logger
        self.encoding = encoding

    async def render_post(self, request):
        # Validate payload
        try:
            payload = json.loads(request.payload.decode(self.encoding))
            if isinstance(payload, dict):
                # Log request to screen
                logging.info(
                    f"{request.code} from {request.remote.uri} ({request.mid})"
                )
                # Log request to disk (JSON payload)
                self.logger.info(json.dumps(payload))
                return aiocoap.Message(
                    code=resource.numbers.codes.CONTENT,
                    payload=b"OK",
                )
            else:
                raise ValueError("Invalid payload, not JSON")
        except Exception as err:
            logging.error(
                f"{request.code} from {request.remote.uri} ({request.mid}): {err}"
            )
            return aiocoap.Message(
                code=resource.numbers.codes.BAD_REQUEST,
                payload=str(err).encode(self.encoding),
            )

    # https://docs.confluent.io/kafka-connectors/spooldir/current/connectors/json_source_connector.html#spooldir-json-source-connector


async def main(
    logger,
    coap_host,
    coap_port,
    coap_path,
    encoding,
):
    # Resource tree creation
    root = resource.Site()

    root.add_resource(
        [".well-known", "core"],
        resource.WKCResource(
            root.get_resources_as_linkheader,
        ),
    )
    root.add_resource(
        [coap_path],
        TelemetryResource(
            logger,
            encoding=encoding,
        ),
    )

    await aiocoap.Context.create_server_context(
        bind=(
            coap_host,
            coap_port,
        ),
        site=root,
    )

    logging.info(f"Started CoAP server on {coap_host}:{coap_port}")

    # Run forever
    await asyncio.get_running_loop().create_future()


if __name__ == "__main__":

    # Load env variables
    load_dotenv(find_dotenv())
    COAP_HOST = os.environ["COAP_HOST"]
    COAP_PORT = int(os.environ["COAP_PORT"])
    COAP_PATH = os.environ["COAP_PATH"]
    COAP_ENCODING = os.environ["COAP_ENCODING"]

    FILE_APP = os.path.splitext(os.path.split(__file__)[-1])[0]
    set_logging_handler(FILE_APP)

    # Log to file
    handler = TimedRotatingFileHandler(
        os.path.join("coap-data", COAP_PATH),
        when="s",
        interval=5,
        backupCount=172800,
        encoding=COAP_ENCODING,
        delay=False,
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(logging.INFO)
    logger = logging.getLogger(FILE_APP)
    logger.addHandler(handler)

    asyncio.run(
        main(
            logger,
            COAP_HOST,
            COAP_PORT,
            COAP_PATH,
            COAP_ENCODING,
        )
    )
