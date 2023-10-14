import re
import time
import json
import unicodedata
from datetime import datetime

from costants import FloorType


def format_amount(value, markdown=False):
    if value is None:
        return "/"
    try:
        if markdown:
            return "{:,.0f}€".format(int(value)).replace(',', '\\.')
        else:
            return "{:,.0f}€".format(int(value)).replace(',', '.')
    except (ValueError, Exception):
        return value


def format_surface(value: int):
    if value is None:
        return "/"
    return f"{int(value)}mq"


def format_boolean(value: bool):
    if value is None:
        return "/"
    return "Sì" if value else "No"


def format_int(value: int):
    if value is None:
        return "/"
    return int(value)


def format_floor(floor):
    if floor is None:
        return FloorType.All.value
    return floor.value


def format_name(username, first_name, last_name):
    name = "NO_NAME"
    if username and username != "":
        name = username
    elif first_name and first_name != "" and last_name and last_name != "":
        name = f"{first_name} {last_name}"
    elif first_name and first_name != "":
        name = f"{first_name}"
    elif last_name and last_name != "":
        name = f"{last_name}"
    return name


def format_text(text):
    if text is None:
        return "/"
    try:
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8').replace('- ', '-').replace(' -', '-').replace(':', ' ').replace('!', ' ').replace('?', '').replace(',', ' ').replace('\'', ' ').replace('<', ' ').replace('>', ' ').replace('\n', ' ').replace('/b', ' ').replace('/', ' ').replace('_', ' ').replace('&', ' ').replace('  ', ' ').replace('  ', ' ')
        text = re.sub(r" ?\([^)]+\)", "", text)
    except (ValueError, Exception):
        pass
    return text


def get_time():
    return int(time.time())


def read_json(filename: str) -> dict or list:
    try:
        with open(filename, 'r') as myfile:
            data = myfile.read()
            obj = json.loads(data)
            return obj
    except FileNotFoundError:
        return False


def write_log(title: str, text: str):
    if not text:
        return
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    with open(f"logs/{title}_{now}.txt", "w") as file:
        file.write(text)
