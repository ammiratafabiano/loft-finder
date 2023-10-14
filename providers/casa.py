import logging
from urllib.parse import urlparse
from urllib.parse import parse_qs
from costants import WatchType, AdvType, FloorType, AdvCategory
from models.watch import Watch, Adv
from services.scraping import scraping
import re

from utils import write_log, format_text


class CasaWatch(Watch):
	def __init__(self, source: str, city: dict, adv_type: AdvType, adv_category: AdvCategory, agency_filter: bool, min_room: int = None,
				max_room: int = None, min_prize: int = None, max_prize: int = None, min_surface: int = None,
				max_surface: int = None, floor: FloorType = FloorType.ALL, description: str = None, url: str = ''):
		super().__init__(source)
		self.display_name = WatchType.CASA.value
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
		raw_list = response.find_all('article', class_='srp-card')
		if not raw_list:
			logging.error("scraping - casa, trying with selenium")
			write_log(self.display_name, response.get_text())
			response = scraping.get_page_with_selenium(self.url)
			raw_list = response.find_all('article', class_='srp-card')
			if not raw_list:
				logging.error("scraping - casa")
				write_log(self.display_name, response.get_text())
				return [], False
		ads = []
		for el in raw_list:
			if el.a is not None:
				url = 'https://' + self.source + el.a.get('href')
				prize_item = el.find('div', class_='info-features__price')
				prize = prize_item.p.get_text() if prize_item.p else prize_item.get_text()
				match = re.findall('[0-9]+', prize.replace('.', ''))
				prize = int(match[0]) if match else prize
				rooms = None
				try:
					raw_rooms = el.find('div', class_='info-features__dtls').div\
						.find_all('div', class_='info-features__item')[1].get_text().lower().replace('locali', '').strip()
					rooms = int(raw_rooms) if raw_rooms.isdigit() else None
				except (ValueError, Exception):
					rooms = None
				if (self.min_rooms and rooms and rooms < self.min_rooms) or (self.max_rooms and rooms and rooms > self.max_rooms):
					continue
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
		if path and path[0] == 'srp':
			temptype = filters.get('tr')[0] if filters.get('tr') else None
			if temptype == 'vendita':
				self.type = AdvType.VENDITA
			elif temptype == 'affitti':
				self.type = AdvType.AFFITTO
		elif path and len(path) == 3:
			if path[0] == 'vendita':
				self.type = AdvType.VENDITA
			elif path[0] == 'affitto':
				self.type = AdvType.AFFITTO
			if path[1] == 'residenziale':
				self.category = AdvCategory.IMMOBILE
			elif path[1] == 'stanze':
				self.category = AdvCategory.STANZA
			self.city = path[-1]
		elif path and len(path) == 4 and 'in-nuove-costruzioni' not in path:
			if path[0] == 'vendita':
				self.type = AdvType.VENDITA
			elif path[0] == 'affitto':
				self.type = AdvType.AFFITTO
			if path[1] == 'residenziale':
				self.category = AdvCategory.IMMOBILE
			elif path[1] == 'stanze':
				self.category = AdvCategory.STANZA
			self.agency_filter = True if path[-1] == 'con-da-privati' else False
			self.city = path[-2]
		elif path and len(path) == 4 and 'in-nuove-costruzioni' in path:
			self.category = AdvCategory.NUOVACOSTRUZIONE
			if path[0] == 'vendita':
				self.type = AdvType.VENDITA
			elif path[0] == 'affitto':
				self.type = AdvType.AFFITTO
			self.city = path[-1]
		temp_auction_filter = filters.get('exclude_auction')[0] if filters.get('exclude_auction') else None
		self.auction_filter = True if temp_auction_filter == 'true' else False
		temp_agency_filter = filters.get('sellerType')[0] if filters.get('sellerType') else None
		self.agency_filter = True if temp_agency_filter == 'privati' else self.agency_filter if temp_agency_filter is None else False
		self.min_rooms = filters.get('numRoomsMin')[0] if filters.get('numRoomsMin') else None
		self.max_rooms = filters.get('numRoomsMax')[0] if filters.get('numRoomsMax') else None
		self.min_prize = filters.get('priceMin')[0] if filters.get('priceMin') else None
		self.max_prize = filters.get('priceMax')[0] if filters.get('priceMax') else None
		self.min_surface = filters.get('mqMin')[0] if filters.get('mqMin') else None
		self.max_surface = filters.get('mqMax')[0] if filters.get('mqMax') else None
		temp_floor_filter = filters.get('level')[0] if filters.get('level') else None
		if temp_floor_filter and temp_floor_filter == 'piano terra':
			self.floor = FloorType.GROUND
		elif temp_floor_filter and temp_floor_filter == 'intermedio':
			self.floor = FloorType.INTERMEDIATE
		elif temp_floor_filter and temp_floor_filter == 'ultimo':
			self.floor = FloorType.LAST
		elif temp_floor_filter and temp_floor_filter.isdigit():
			if int(temp_floor_filter) > 0:
				self.floor = FloorType.INTERMEDIATELAST

	def set_url(self):
		if self.source and self.city and self.type and self.category:
			category = "residenziale"
			if self.category == AdvCategory.STANZA:
				category = "stanze"
			elif self.category == AdvCategory.NUOVACOSTRUZIONE:
				category = "residenziale/in-nuove-costruzioni"

			city = "-".join(format_text(self.city.lower()).split(" "))

			agency_filter = "/con-da-privati/" if self.agency_filter else "/"
			params = "?"
			if self.auction_filter is True:
				params += "exclude_auction=true&"
			if self.min_prize:
				params += f"priceMin={self.min_prize}&"
			if self.max_prize:
				params += f"priceMax={self.max_prize}&"
			if self.min_surface:
				params += f"mqMin={self.min_surface}&"
			if self.max_surface:
				params += f"mqMax={self.max_surface}&"
			if self.floor:
				if self.floor == FloorType.GROUND:
					params += f"level=piano+terra&"
				elif self.floor == FloorType.INTERMEDIATE:
					params += f"level=intermedio&"
				elif self.floor == FloorType.LAST:
					params += f"level=ultimo&"
				elif self.floor == FloorType.INTERMEDIATELAST:
					params += f"level=1&"
			url = f"https://{self.source}/{self.type.value.lower()}/{category}/{city}{agency_filter}{params}" \
				f"sortType=date_desc"
			self.url = url
