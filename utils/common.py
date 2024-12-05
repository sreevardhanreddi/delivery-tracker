import json
from datetime import datetime

from loguru import logger


def dict_to_str(d: dict) -> str:
    s = ""
    for k, v in d.items():
        s += f"{k}: {v}\n"
    return "\n" + s


def parse_date_time_string(date_time_string):
    date_formats = [
        "%Y-%m-%d %H:%M:%S",  # Format: 2024-12-05 11:03:59
        "%d %b %Y %H:%M",  # Format: 07 Oct 2024 22:24
        "%d-%m-%Y %H:%M:%S",  # Format: 05-12-2024 11:03:59
    ]

    # Try each format
    for date_format in date_formats:
        try:
            return datetime.strptime(date_time_string, date_format)
        except Exception as e:
            # logger.error(f"An error occurred parsing the date: {e}")
            continue

    return None


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(obj)


def json_dumps(obj):
    return json.dumps(obj, cls=DateTimeEncoder)
