import os
import sys
import time
import socket
import logging

from dotenv import load_dotenv, find_dotenv
from cefevent import CEFEvent
from datetime import datetime
from pysyslogclient import SyslogClient, FAC_USER, SEV_NOTICE

from utils import (
    sys_exc,
    round_temp,
    get_delta_temp,
    get_epoch_milli,
    get_next_interval,
    set_logging_handler,
    get_details,
)


class SyslogClientRFC3164(SyslogClient):
    def __init__(
        self,
        host: str,
        port: int,
        protocol: str,
        device_product: str,
        device_vendor: str,
        device_serial_number: str,
        forceipv4: bool = False,
        clientname: str = None,
    ) -> None:
        SyslogClient.__init__(
            self,
            server=host,
            port=port,
            proto=protocol,
            forceipv4=forceipv4,
            clientname=clientname,
            rfc="3164",
            maxMessageLength=1024,
        )
        self.device_vendor = device_vendor
        self.device_product = device_product
        self.device_serial_number = device_serial_number
        self.host_name = socket.getfqdn()
        if self.host_name == None:
            self.host_name = socket.gethostname()

        self.is_connected = False

    def sys_connect(self) -> None:
        try:
            self.is_connected = self.connect()
        except Exception:
            logging.error(sys_exc(sys.exc_info()))
            self.is_connected = False
            time.sleep(1)

    def cef_message(
        self,
        severity: int,
        signature_id: int,
        location: str,
        lat: float,
        lng: float,
        temperature: float,
        unit: str,
    ):
        c = CEFEvent(strict=True)
        c.set_field("version", "0")
        c.set_field("name", "Telemetry")
        c.set_field("deviceVendor", self.device_vendor)
        c.set_field("deviceProduct", self.device_product)
        c.set_field("deviceVersion", self.device_serial_number)
        c.set_field("signatureId", str(signature_id))
        c.set_field("severity", severity)
        # Extensions: https://github.com/kamushadenes/cefevent/blob/master/cefevent/extensions.py
        c.set_field("deviceCustomFloatingPoint1", temperature)
        c.set_field("deviceCustomFloatingPoint1Label", unit)
        c.set_field("deviceCustomFloatingPoint2", lat)
        c.set_field("deviceCustomFloatingPoint2Label", "lat")
        c.set_field("deviceCustomFloatingPoint3", lng)
        c.set_field("deviceCustomFloatingPoint3Label", "lon")
        c.set_field("deviceDirection", location)
        return c.build_cef()

    def log(
        self,
        temperature: float,
        location: str,
        lat: float,
        lng: float,
        timestamp: datetime = None,
        facility: int = FAC_USER,
        severity: int = SEV_NOTICE,
        unit: str = "C",
    ) -> str:
        pri = facility * 8 + severity

        if timestamp is None:
            timestamp = datetime.now()

        message = self.cef_message(
            severity,
            100,
            location,
            lat,
            lng,
            temperature,
            unit,
        )
        syslog_data = "<%i>%s %s %s\n" % (
            pri,
            timestamp.strftime("%b %d %H:%M:%S"),
            self.host_name,
            message,
        )

        self.send(syslog_data.encode("ASCII", "ignore"))

        return syslog_data  # Example: <13>Apr 01 18:54:54 P3W32CDKHC CEF:0|SysTemp|SysIotLog|369f9aa5df41|100|Telemetry|5|cfp1=27.0156 cfp1Label=C deviceDirection=Region_25


if __name__ == "__main__":

    FILE_APP = os.path.splitext(os.path.split(__file__)[-1])[0]
    set_logging_handler(FILE_APP)

    # Load env variables
    load_dotenv(find_dotenv())
    SYSLOG_HOST = os.environ["SYSLOG_HOST"]
    SYSLOG_PORT = int(os.environ["SYSLOG_PORT"])
    SYSLOG_PROTOCOL = os.environ["SYSLOG_PROTOCOL"]
    SYSLOG_DEVICES = min(25, int(os.environ["SYSLOG_DEVICES"]))
    SYSLOG_MIN_ITERVAL_MS = int(os.environ["SYSLOG_MIN_ITERVAL_MS"])
    SYSLOG_MAX_ITERVAL_MS = int(os.environ["SYSLOG_MAX_ITERVAL_MS"])

    SEED = "#Syslog"
    MANUFACTURER = "SysIotLog"
    DEVICE_FAMILY = "SysTemp"

    # Devices cache
    devices = dict()
    for _id in range(SYSLOG_DEVICES):
        serial_number, location, temp_mu, temp_sigma = get_details(_id, SEED)
        devices[_id] = {
            "serial_number": serial_number,
            "temperature": get_delta_temp(temp_mu, temp_sigma),
            "unit": "C",
            "last_sent": get_next_interval(
                SYSLOG_MIN_ITERVAL_MS,
                SYSLOG_MAX_ITERVAL_MS,
            ),
            "location": location,
            "client": SyslogClientRFC3164(
                SYSLOG_HOST,
                SYSLOG_PORT,
                SYSLOG_PROTOCOL,
                MANUFACTURER,
                DEVICE_FAMILY,
                serial_number,
            ),
        }

    # Main thread loop
    try:
        while True:
            for _id in range(SYSLOG_DEVICES):
                if devices[_id]["client"].is_connected:
                    try:
                        if devices[_id]["last_sent"] < time.time():
                            devices[_id]["temperature"] = round_temp(
                                devices[_id]["temperature"] + get_delta_temp()
                            )

                            timestamp = get_epoch_milli()
                            syslog_data = devices[_id]["client"].log(
                                temperature=devices[_id]["temperature"],
                                location=devices[_id]["location"]["city"],
                                lat=devices[_id]["location"]["lat"],
                                lng=devices[_id]["location"]["lng"],
                                unit=devices[_id]["unit"],
                            )

                            logging.info(f"Syslog message sent:{syslog_data}")

                            devices[_id]["last_sent"] = get_next_interval(
                                SYSLOG_MIN_ITERVAL_MS,
                                SYSLOG_MAX_ITERVAL_MS,
                            )
                            time.sleep(0.01)

                    except (BrokenPipeError, ConnectionRefusedError):
                        logging.error(sys_exc(sys.exc_info()))
                        devices[_id]["client"].sys_connect()
                        time.sleep(1)
                        break

                    except Exception:
                        logging.error(sys_exc(sys.exc_info()))
                        logging.error(
                            f"Error when sending message from device ({devices[_id]['serial_number']}))"
                        )

                else:
                    devices[_id]["client"].sys_connect()

            time.sleep(0.05)

    except KeyboardInterrupt:
        logging.info("CTRL-C pressed by user")

    finally:
        logging.info("Stopped SysLog client")
