import time
import random
import hashlib
import logging

from datetime import datetime,timezone


def set_logging_handler(
    app_name: str,
    level: int = logging.INFO,
) -> None:
    logging.basicConfig(
        format=f"[{app_name}] %(asctime)s.%(msecs)03d [%(levelname)s]: %(message)s",
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def sys_exc(exc_info) -> str:
    exc_type, exc_obj, exc_tb = exc_info
    return f"{exc_type} | {exc_tb.tb_lineno} | {exc_obj}"


def get_epoch_milli() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_isotimestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")


def round_temp(t: float) -> float:
    return float(f"{t:.4f}")


def get_delta_temp(mu: float = 0, sigma: float = 0.01) -> float:
    return round_temp(random.gauss(mu, sigma))


def get_next_interval(a: int, b: int) -> float:
    return time.time() + random.randint(a, b) / 1000


def generate_serial_number(
    id: int,
    seed: str,
    length: int = 12,
) -> str:
    return hashlib.sha1(f"{id}_{seed}".encode("utf-8")).hexdigest()[:length]


def get_details(id: int, seed: str) -> tuple:
    serial_number = generate_serial_number(id, seed)
    seed_loc = int(serial_number, 16) % 100
    location = f"Region_{seed_loc:02d}"
    temp_mu = 31 - seed_loc % 19
    temp_sigma = 0.05
    return (
        serial_number,
        location,
        temp_mu,
        temp_sigma,
    )


def generate_payload(
    temperature: float,
    manufacturer: str = None,
    dev_family: str = None,
    location: str = None,
    serial_number: str = None,
    unit: str = None,
    timestamp_key: str = "timestamp",
    temperature_key: str = "temperature",
    manufacturer_key: str = "manufacturer",
    dev_family_key: str = "dev_family",
    serial_number_key: str = "serial_number",
    location_key: str = "location",
    unit_key: str = "unit",
    _timestamp_epoch: bool = True,
) -> dict:
    local_vars = dict(locals())
    if _timestamp_epoch:
        timestamp = get_epoch_milli()
    else:
        timestamp = get_isotimestamp()
    result = {
        timestamp_key: timestamp,
    }
    for key, value in local_vars.items():
        if not key.endswith("_key") and not key.startswith("_"):
            if value is not None:
                result[local_vars[f"{key}_key"]] = value
    return result
