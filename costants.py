from enum import Enum


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


ADMIN_ID = 88654383
BOT_TOKEN = 'BOT_TOKEN'
