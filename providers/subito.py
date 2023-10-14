import logging
from urllib.parse import urlparse
from urllib.parse import parse_qs
from costants import WatchType, AdvType, FloorType, AdvCategory
from models.watch import Watch, Adv
from services.scraping import scraping
import re

from utils import write_log, format_text


class SubitoWatch(Watch):
	def __init__(self, source: str, city: dict, adv_type: AdvType, adv_category: AdvCategory, agency_filter: bool, min_room: int = None,
				max_room: int = None, min_prize: int = None, max_prize: int = None, min_surface: int = None,
				max_surface: int = None, floor: FloorType = FloorType.ALL, description: str = None, url: str = ''):
		super().__init__(source)
		self.display_name = WatchType.SUBITO.value
		self.description = description
		self.first_execution = True
		self.status = True
		if not url:
			self.__set_default_filter()
			self.source = source
			self.city = city["nome"]
			self.province = city["provincia"]["nomeSubito"] if hasattr(city["provincia"], 'nomeSubito') else city["provincia"]["nome"]
			self.region = city["regione"]["nome"]
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
		raw_list = response.find_all('div', class_='items__item')
		if not raw_list:
			logging.error("scraping - subito, trying with selenium")
			write_log(self.display_name, response.get_text())
			response = scraping.get_page_with_selenium(self.url)
			raw_list = response.find_all('div', class_='items__item')
			if not raw_list:
				logging.error("scraping - subito")
				write_log(self.display_name, response.get_text())
				return [], False
		ads = []
		for el in raw_list:
			if el.a is not None:
				url = el.a.get('href')
				prize_item = el.find('p')
				prize = prize_item.get_text() if prize_item else None
				if not prize:
					continue
				if 'mq' in prize:
					prize = 'Trattativa riservata'
				else:
					match = re.findall('[0-9]+', prize.replace('.', ''))
					prize = int(match[0]) if match else prize
				new_adv = Adv(self.display_name, url, prize)
				ads.append(new_adv)
		return ads, True

	def __set_default_filter(self):
		self.type = None
		self.category = None
		self.city = None
		self.agency_filter = None
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
		self.city = path[-1].capitalize() if path else None
		self.province = path[-2].capitalize() if path else None
		temp_region = path[0].split('-') if path else None
		self.region = temp_region[1] if temp_region else None
		if path and path[1] == 'vendita':
			self.type = AdvType.VENDITA
		elif path and path[1] == 'affitto':
			self.type = AdvType.AFFITTO
		if path and path[2] == 'appartamenti':
			self.category = AdvCategory.IMMOBILE
		elif path and path[2] == 'camere-posti-letto':
			self.category = AdvCategory.STANZA
		self.category = AdvCategory.NUOVACOSTRUZIONE if filters.get('bc') == '10' else self.category
		temp_agency_filter = filters.get('advt')[0] if filters.get('advt') else None
		self.agency_filter = True if temp_agency_filter == '0' else False
		self.min_rooms = filters.get('rs')[0] if filters.get('rs') else None
		self.max_rooms = filters.get('re')[0] if filters.get('re') else None
		self.min_prize = filters.get('ps')[0] if filters.get('ps') else None
		self.max_prize = filters.get('pe')[0] if filters.get('pe') else None
		self.min_surface = filters.get('szs')[0] if filters.get('szs') else None
		self.max_surface = filters.get('sze')[0] if filters.get('sze') else None
		temp_min_floor = filters.get('fls')[0] if filters.get('fls') else None
		temp_max_floor = filters.get('fle')[0] if filters.get('fle') else None
		if temp_min_floor and temp_min_floor.isdigit() and int(temp_min_floor) in [3, 4] \
			and (not temp_max_floor or (temp_max_floor.isdigit() and int(temp_max_floor) in [3, 4])):
			self.floor = FloorType.GROUND
		if temp_min_floor and temp_min_floor.isdigit() and int(temp_min_floor) > 4:
			self.floor = FloorType.INTERMEDIATELAST

	def set_url(self):
		if self.source and self.city and self.type and self.category:
			category = 'immobili'
			if self.category == AdvCategory.STANZA:
				category = 'camere-posti-letto'

			city = "-".join(format_text(self.city.lower()).split(" "))
			province = "-".join(format_text(self.province.lower()).split(" "))
			region = "-".join(format_text(self.region.lower()).split(" "))

			params = "?"
			if self.category == AdvCategory.NUOVACOSTRUZIONE:
				params += "bc=10&"
			if self.agency_filter is True:
				params += "advt=0&"
			if self.min_rooms:
				params += f"rs={self.min_rooms}&"
			if self.max_rooms:
				params += f"re={self.max_rooms}&"
			if self.min_prize:
				params += f"ps={self.min_prize}&"
			if self.max_prize:
				params += f"pe={self.max_prize}&"
			if self.min_surface:
				params += f"szs={self.min_surface}&"
			if self.max_surface:
				params += f"sze={self.max_surface}&"
			if self.floor == FloorType.GROUND:
				params += "fls=3&fle=4&"
			if self.floor == FloorType.INTERMEDIATE or self.floor == FloorType.INTERMEDIATELAST or self.floor == FloorType.LAST:
				params += "fls=5"
			if params == "?":
				params = ""

			url = f"https://{self.source}/annunci-{region}/{self.type.value.lower()}/{category}" \
				f"/{province}/{city}/{params}"
			self.url = url
