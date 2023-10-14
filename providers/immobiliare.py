import logging
from urllib.parse import urlparse
from urllib.parse import parse_qs

from costants import WatchType, AdvType, FloorType, AdvCategory
from models.watch import Watch, Adv
from services.scraping import scraping
import re

from utils import write_log, format_text


class ImmobiliareWatch(Watch):
    def __init__(self, source: str, city: dict, adv_type: AdvType, adv_category: AdvCategory,
                 agency_filter: bool, min_room: int = None, max_room: int = None, min_prize: int = None,
                 max_prize: int = None, min_surface: int = None, max_surface: int = None,
                 floor: FloorType = FloorType.ALL, description: str = None, url: str = ''):
        super().__init__(source)
        self.display_name = WatchType.IMMOBILIARE.value
        self.description = description
        self.first_execution = True
        self.status = True
        if not url:
            self.__set_default_filter()
            self.source = source
            self.city = city["nome"]
            self.type = adv_type
            self.category = adv_category
            self.agency_filter = agency_filter
            self.min_rooms = min_room
            self.max_rooms = max_room
            self.min_prize = min_prize
            self.max_prize = max_prize
            self.min_surface = min_surface
            self.max_surface = max_surface
            self.floor = floor
            self.set_url()
        else:
            self.url = url
            self.__set_filters()

    def get_ads(self):
        response = scraping.get_page_with_requests(self.url)
        raw_list = response.find_all('li', class_='nd-list__item in-realEstateResults__item')
        if not raw_list:
            logging.error("scraping - immobiliare, trying with selenium")
            write_log(self.display_name, response.get_text())
            response = scraping.get_page_with_selenium(self.url)
            raw_list = response.find_all('li', class_='nd-list__item in-realEstateResults__item')
            if not raw_list:
                logging.error("scraping - immobiliare")
                write_log(self.display_name, response.get_text())
                return [], False
        ads = []
        for raw_adv in raw_list:
            temp = raw_adv.a
            if temp is not None:
                url = temp.get('href')
                prize = raw_adv.find('li', class_='in-feat__item--main').get_text(separator=' ')
                match = re.findall('[0-9]+', prize.replace('.', ''))
                prize = int(match[0]) if match else prize
                agency = raw_adv.find('div', class_='in-realEstateListCard__referent')
                if not self.agency_filter or (self.agency_filter and not agency):
                    new_adv = Adv(self.display_name, url, prize)
                    ads.append(new_adv)
        return ads, True

    def __set_default_filter(self):
        self.type = None
        self.category = None
        self.city = None
        self.agency_filter = None
        self.auction_filter = None
        self.min_rooms = None
        self.max_rooms = None
        self.min_prize = None
        self.max_prize = None
        self.min_surface = None
        self.max_surface = None
        self.floor = None

    def __set_filters(self):
        filters = parse_qs(urlparse(self.url).query)
        temp_path = urlparse(self.url).path
        path = temp_path.strip('/').split('/') if temp_path else None
        self.city = path[1].capitalize() if path and len(path) > 1 else None
        if path and path[0] == 'vendita-case':
            self.type = AdvType.VENDITA
            self.category = AdvCategory.IMMOBILE
        elif path and path[0] == 'affitto-case':
            self.type = AdvType.AFFITTO
            self.category = AdvCategory.IMMOBILE
        elif path and path[0] == 'affitto-stanze':
            self.type = AdvType.AFFITTO
            self.category = AdvCategory.STANZA
        elif path and path[0] == 'nuove-costruzioni':
            self.type = AdvType.AFFITTO
            self.category = AdvCategory.IMMOBILE
        temp_auction_filter = filters.get('noAste')[0] if filters.get('noAste') else None
        self.auction_filter = True if temp_auction_filter == '1' else False
        self.min_rooms = filters.get('localiMinimo')[0] if filters.get('localiMinimo') else None
        self.max_rooms = filters.get('localiMassimo')[0] if filters.get('localiMassimo') else None
        self.min_prize = filters.get('prezzoMinimo')[0] if filters.get('prezzoMinimo') else None
        self.max_prize = filters.get('prezzoMassimo')[0] if filters.get('prezzoMassimo') else None
        self.min_surface = filters.get('superficieMinima')[0] if filters.get('superficieMinima') else None
        self.max_surface = filters.get('superficieMassima')[0] if filters.get('superficieMassima') else None
        temp_floor_filter = path[2] if path and len(path) > 2 else None
        temp_floor_filter_2 = filters.get('fasciaPiano[]')[0] if filters.get('fasciaPiano[]') else None
        if temp_floor_filter and temp_auction_filter == 'con-piano-terra':
            self.floor = FloorType.GROUND
        if temp_floor_filter and temp_auction_filter == 'con-piani-intermedi':
            self.floor = FloorType.INTERMEDIATE
        if temp_floor_filter and temp_auction_filter == 'con-ultimo-piano':
            self.floor = FloorType.LAST
        if (temp_floor_filter and temp_auction_filter == 'con-piani-intermedi'
                and temp_floor_filter_2 and temp_floor_filter_2 == "30") \
            or (temp_floor_filter and temp_auction_filter == 'con-ultimo-piano'
                and temp_floor_filter_2 and temp_floor_filter_2 == "20"):
            self.floor = FloorType.INTERMEDIATELAST

    def set_url(self):
        if self.source and self.city and self.type and self.category:
            category_type = 'vendita-case'
            if self.type == AdvType.AFFITTO and self.category == AdvCategory.IMMOBILE:
                category_type = 'affitto-case'
            elif self.type == AdvType.AFFITTO and self.category == AdvCategory.STANZA:
                category_type = 'affitto-stanze'
            elif self.type == AdvType.VENDITA and self.category == AdvCategory.NUOVACOSTRUZIONE:
                category_type = 'nuove-costruzioni'

            city = "-".join(format_text(self.city.lower()).split(" "))

            params = "?"
            if self.auction_filter is True:
                params += "noAste=1&"
            if self.min_rooms:
                params += f"localiMinimo={self.min_rooms}&"
            if self.max_rooms:
                params += f"localiMassimo={self.max_rooms}&"
            if self.min_prize:
                params += f"prezzoMinimo={self.min_prize}&"
            if self.max_prize:
                params += f"prezzoMassimo={self.max_prize}&"
            if self.min_surface:
                params += f"superficieMinima={self.min_surface}&"
            if self.max_surface:
                params += f"superficieMassima={self.max_surface}&"
            if self.floor == FloorType.GROUND:
                params += "fasciaPiano[]=10&"
            if self.floor == FloorType.INTERMEDIATE:
                params += "fasciaPiano[]=20&"
            if self.floor == FloorType.LAST:
                params += "fasciaPiano[]=30&"
            if self.floor == FloorType.INTERMEDIATELAST:
                params += "fasciaPiano[]=20&fasciaPiano[]=30&"

            url = f"https://{self.source}/{category_type}/{city}/{params}" \
                f"criterio=dataModifica&ordine=desc"
            self.url = url
