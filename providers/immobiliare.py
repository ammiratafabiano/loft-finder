import json
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

    @staticmethod
    def _parse_next_data(soup):
        """Estrae i risultati dal JSON __NEXT_DATA__ embeddato nelle pagine Next.js di Immobiliare.it"""
        script_tag = soup.find('script', id='__NEXT_DATA__', type='application/json')
        if not script_tag:
            return None
        try:
            data = json.loads(script_tag.string)
        except (json.JSONDecodeError, TypeError):
            return None

        # Naviga ricorsivamente il JSON cercando array "results" con chiave "realEstate"
        def find_results(obj, depth=0):
            if depth > 10:
                return None
            if isinstance(obj, dict):
                if 'results' in obj and isinstance(obj['results'], list):
                    candidates = obj['results']
                    if candidates and isinstance(candidates[0], dict) and 'realEstate' in candidates[0]:
                        return candidates
                for v in obj.values():
                    found = find_results(v, depth + 1)
                    if found is not None:
                        return found
            elif isinstance(obj, list):
                for item in obj:
                    found = find_results(item, depth + 1)
                    if found is not None:
                        return found
            return None

        return find_results(data)

    def get_ads(self):
        response = scraping.get_page_with_requests(self.url)

        # --- Tentativo 1: __NEXT_DATA__ JSON (immune ai cambi di classi CSS) ---
        results = self._parse_next_data(response)
        if results is not None:
            ads = self._ads_from_next_data(results)
            logging.info(f"immobiliare __NEXT_DATA__: {len(results)} results -> {len(ads)} ads")
            if ads or len(results) == 0:
                return ads, True
            # Se results non è vuoto ma ads sì, probabile cambio struttura JSON: prova HTML
            logging.warning(f"immobiliare __NEXT_DATA__ found {len(results)} results but 0 ads, trying HTML")

        # --- Tentativo 2: HTML parsing classico ---
        raw_list = response.find_all('li', class_=re.compile(
            r'nd-list__item|in-realEstateResults__item|in-searchList__item'))
        if raw_list:
            return self._ads_from_html(raw_list), True

        # --- Tentativo 3: Selenium con __NEXT_DATA__ ---
        logging.error("scraping - immobiliare, trying with selenium")
        write_log(self.display_name, response.get_text())
        response = scraping.get_page_with_selenium(self.url)

        results = self._parse_next_data(response)
        if results is not None:
            ads = self._ads_from_next_data(results)
            logging.info(f"immobiliare selenium __NEXT_DATA__: {len(results)} results -> {len(ads)} ads")
            if ads or len(results) == 0:
                return ads, True

        raw_list = response.find_all('li', class_=re.compile(
            r'nd-list__item|in-realEstateResults__item|in-searchList__item'))
        if raw_list:
            return self._ads_from_html(raw_list), True

        logging.error("scraping - immobiliare")
        write_log(self.display_name, response.get_text())
        return [], False

    def _ads_from_next_data(self, results):
        ads = []
        for item in results:
            re_data = item.get('realEstate', {})
            if not re_data:
                continue
            # URL: prova più path nel JSON (la struttura cambia spesso)
            url = ''
            # 1. properties[0].url (struttura vecchia)
            props = re_data.get('properties', [])
            if props and isinstance(props[0], dict):
                url = props[0].get('url', '')
            # 2. realEstate.url diretto
            if not url:
                url = re_data.get('url', '')
            # 3. seo.url o seo.anchor (struttura Next.js recente)
            if not url:
                seo = re_data.get('seo', {})
                if isinstance(seo, dict):
                    url = seo.get('url', '') or seo.get('anchor', '')
            # 4. permalink / link
            if not url:
                url = re_data.get('permalink', '') or re_data.get('link', '')
            # 5. Costruisci dall'id come fallback
            if not url and re_data.get('id'):
                url = f"https://www.immobiliare.it/annunci/{re_data['id']}/"
            if not url:
                continue
            if not url.startswith('http'):
                url = f"https://{self.source}{url}"
            # Prezzo
            price_obj = re_data.get('price', {})
            prize = price_obj.get('value', 0) if isinstance(price_obj, dict) else 0
            if not prize:
                prize = price_obj.get('formattedValue', '0') if isinstance(price_obj, dict) else '0'
                match = re.findall(r'[0-9]+', str(prize).replace('.', ''))
                prize = int(match[0]) if match else prize
            # Filtro agenzie
            agency = re_data.get('agency') or re_data.get('advertiser', {})
            has_agency = bool(agency)
            if not self.agency_filter or (self.agency_filter and not has_agency):
                ads.append(Adv(self.display_name, url, prize))
        return ads

    def _ads_from_html(self, raw_list):
        ads = []
        for raw_adv in raw_list:
            temp = raw_adv.find('a', href=True)
            if temp is not None:
                url = temp.get('href')
                prize_elem = raw_adv.find(string=re.compile(r'€'))
                if not prize_elem:
                    prize_elem = raw_adv.find('li', class_=re.compile(r'in-feat__item|price'))
                    prize = prize_elem.get_text(separator=' ') if prize_elem else "0"
                else:
                    prize = prize_elem.parent.get_text(separator=' ')
                match = re.findall('[0-9]+', prize.replace('.', ''))
                prize = int(match[0]) if match else prize
                agency = raw_adv.find('div', class_=re.compile(r'in-realEstateListCard__referent|in-card__referent'))
                if not self.agency_filter or (self.agency_filter and not agency):
                    ads.append(Adv(self.display_name, url, prize))
        return ads

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
