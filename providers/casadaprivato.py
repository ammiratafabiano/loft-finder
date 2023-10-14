import logging
import math
from urllib.parse import urlparse
from costants import WatchType, AdvType, AdvCategory
from models.watch import Watch, Adv
from services.scraping import scraping
import re

from utils import write_log, format_text


class CasaDaPrivatoWatch(Watch):
    def __init__(self, source: str, city: dict, adv_type: AdvType, adv_category: AdvCategory, min_room: int = None,
                 max_room: int = None, min_prize: int = None, max_prize: int = None, min_surface: int = None,
                 max_surface: int = None, description: str = None, url: str = ''):
        super().__init__(source)
        self.display_name = WatchType.CASADAPRIVATO.value
        self.description = description
        self.first_execution = True
        self.status = True
        if not url:
            self.__set_default_filter()
            self.source = source
            self.city = city["nome"]
            self.province = city["provincia"]["nome"]
            self.type = adv_type
            self.category = adv_category
            self.min_rooms = min_room
            self.max_rooms = max_room
            self.min_prize = min_prize
            self.max_prize = max_prize
            self.min_surface = min_surface
            self.max_surface = max_surface
            self.set_url()
        else:
            self.url = url
            self.__set_filters()

    def get_ads(self):
        response = scraping.get_page_with_requests(self.url)
        raw_list = response.find_all('div', class_='item')
        raw_exclude = response.find_all('div', class_='ve')
        if not raw_list:
            logging.error("scraping - casadaprivato, trying with selenium")
            write_log(self.display_name, response.get_text())
            response = scraping.get_page_with_selenium(self.url)
            raw_list = response.find_all('div', class_='item')
            raw_exclude = response.find_all('div', class_='ve')
            if not raw_list:
                logging.error("scraping - casadaprivato")
                write_log(self.display_name, response.get_text())
                return [], False
        ads = []
        for el in raw_list:
            if el not in raw_exclude:
                if el.a is not None:
                    url = 'https://' + self.source + el.a.get('href')
                    prize = el.find('div', class_='price').span.get_text()
                    match = re.findall('[0-9]+', prize.replace('.', ''))
                    prize = int(match[0]) if match else prize
                    if (self.min_prize and prize and str(prize).isdigit() and prize < self.min_prize) \
                            or (self.max_prize and prize and str(prize).isdigit() and prize > self.max_prize):
                        continue
                    raw_rooms = None
                    try:
                        raw_rooms = el.find('ul', class_='amenities').li.get_text().lower()
                    except (ValueError, Exception):
                        raw_rooms = None
                    rooms = None
                    if raw_rooms:
                        if 'monolocale' in raw_rooms or '1' in raw_rooms:
                            rooms = 1
                        elif 'bilocale' in raw_rooms or '2' in raw_rooms:
                            rooms = 2
                        elif 'trilocale' in raw_rooms or '3' in raw_rooms:
                            rooms = 3
                        elif 'quadrilocale' in raw_rooms or '4' in raw_rooms:
                            rooms = 4
                        elif '5 locali' in raw_rooms:
                            rooms = 5
                        else:
                            rooms = math.inf
                        if (self.min_rooms and rooms and rooms < self.min_rooms) \
                                or (self.max_rooms and rooms and rooms > self.max_rooms):
                            continue
                    surface = None
                    try:
                        raw_surface = el.find('ul', class_='amenities').find_all('li')[
                            1].get_text().lower().replace('mq', '').strip()
                        surface = int(raw_surface) if raw_surface.isdigit() else None
                    except (ValueError, Exception):
                        surface = None
                    if (self.min_surface and surface and surface < self.min_surface) \
                            or (self.max_surface and surface and surface > self.max_surface):
                        continue
                    new_adv = Adv(self.display_name, url, prize)
                    ads.append(new_adv)
        return ads, True

    def __set_default_filter(self):
        self.type = None
        self.category = None
        self.city = None
        self.min_rooms = None
        self.max_rooms = None
        self.min_prize = None
        self.max_prize = None
        self.min_surface = None
        self.max_surface = None

    def __set_filters(self):
        temp_path = urlparse(self.url).path
        path = temp_path.strip('/').split('/') if temp_path else None
        temp_city = path[-1].split('-') if path else None
        self.city = temp_city[1].capitalize() if temp_city else None
        self.province = temp_city[0] if temp_city else None
        if path and path[0] == 'annunci-vendita':
            self.type = AdvType.VENDITA
        elif path and path[0] == 'annunci-affitto':
            self.type = AdvType.AFFITTO
        if path and path[1] == 'stanze-posti-letto':
            self.category = AdvCategory.STANZA
        elif path and path[1] == 'nuove-costruzioni':
            self.category = AdvCategory.NUOVACOSTRUZIONE
        elif path and path[1] == 'immobili':
            self.category = AdvCategory.IMMOBILE

    def set_url(self):
        if self.source and self.city and self.type and self.category:
            city = "_".join(format_text(self.city.lower()).split(" "))
            province = "_".join(format_text(self.province.lower()).split(" "))

            category = "immobili"
            if self.category == AdvCategory.STANZA:
                category = "stanze-posti-letto"
            elif self.category == AdvCategory.NUOVACOSTRUZIONE:
                category = "nuove-costruzioni"

            url = f"https://{self.source}/annunci-{self.type.value.lower()}/{category}" \
                  f"/{province}-{city}/?sort=data-desc"
            self.url = url
