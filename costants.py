import json
import os
from enum import Enum
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "config.json"

class AdvType(Enum):
    AFFITTO = 'Affitto'
    VENDITA = 'Vendita'


class AdvCategory(Enum):
    IMMOBILE = 'Intero immobile'
    STANZA = 'Stanza/Posto Letto'
    NUOVACOSTRUZIONE = 'Nuova Costruzione'


class WatchType(Enum):
    CASA = 'Casa'
    CASADAPRIVATO = 'CasaDaPrivato'
    IDEALISTA = 'Idealista'
    IMMOBILIARE = 'Immobiliare'
    SUBITO = 'Subito'


class UrlWatchType(Enum):
    CASA = 'www.casa.it'
    CASADAPRIVATO = 'www.casadaprivato.it'
    IDEALISTA = 'www.idealista.it'
    IMMOBILIARE = 'www.immobiliare.it'
    SUBITO = 'www.subito.it'


class ShortAnswer(Enum):
    YES = 'Sì'
    NO = 'No'


class FloorType(Enum):
    GROUND = 'Terra'
    INTERMEDIATE = 'Intermedio'
    INTERMEDIATELAST = 'Intermedio/Ultimo'
    LAST = 'Ultimo'
    ALL = 'Tutti'

# Load config
config_data = {}
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")

# Values come exclusively from config.json
ADMIN_ID = int(config_data.get('ADMIN_ID', 0))
BOT_TOKEN = config_data.get('BOT_TOKEN', "")
