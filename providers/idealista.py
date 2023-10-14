import json
import logging
import math
from datetime import datetime
from urllib.parse import urlparse
from costants import WatchType, AdvType, FloorType, AdvCategory
from models.watch import Watch, Adv
from services.scraping import scraping
import re

from utils import write_log, format_text


class IdealistaWatch(Watch):
	def __init__(self, source: str, city: dict, adv_type: AdvType, adv_category: AdvCategory, agency_filter: bool, min_room: int = None,
				max_room: int = None, min_prize: int = None, max_prize: int = None, min_surface: int = None,
				max_surface: int = None, floor: FloorType = FloorType.ALL, description: str = None, url: str = ''):
		super().__init__(source)
		self.display_name = WatchType.IDEALISTA.value
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
		raw_list = response.find_all('article', class_='item')
		if not raw_list:
			logging.error("scraping - idealista, trying with selenium")
			write_log(self.display_name, response.get_text())
			response = scraping.get_page_with_selenium(self.url)
			raw_list = response.find_all('article', class_='item')
			if not raw_list:
				logging.error("scraping - idealista")
				write_log(self.display_name, response.get_text())
				return [], False
		ads = []
		for el in raw_list:
			if self.agency_filter and "item_contains_branding" in el["class"]:
				continue
			url_item = el.find('a', class_='item-link')
			if url_item:
				url = 'https://' + self.source + url_item.get('href')
				prize = el.find('span', class_='item-price').get_text()
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
		self.auction_filter = None
		self.min_rooms = None
		self.max_rooms = None
		self.min_prize = None
		self.max_prize = None
		self.min_surface = None
		self.max_surface = None
		self.floor = None

	def __set_filters(self):
		temp_path = urlparse(self.url).path
		path = temp_path.strip('/').split('/') if temp_path else None
		temp_city = path[1].split('-') if path and len(path) > 1 else None
		self.city = temp_city[1].capitalize() if temp_city else None
		self.province = temp_city[0].capitalize() if temp_city else None
		if path and path[0] == 'vendita-case':
			self.type = AdvType.VENDITA
			self.category = AdvCategory.IMMOBILE
		elif path and path[0] == 'affitto-case':
			self.type = AdvType.AFFITTO
			self.category = AdvCategory.IMMOBILE
		elif path and path[0] == 'vendita-nuove_costruzioni':
			self.type = AdvType.VENDITA
			self.category = AdvCategory.NUOVACOSTRUZIONE
		elif path and path[0] == 'affitto-stanze':
			self.type = AdvType.AFFITTO
			self.category = AdvCategory.STANZA

		tempparams = path[-1] if path else None
		params = tempparams.split(',') if tempparams else None
		for param in params:
			if 'monolocali-1' in param:
				self.min_rooms = 1
			if 'bilocali-2' in params:
				self.min_rooms = 2
			if 'trilocali-3' in params:
				self.min_rooms = 3
			if 'quadrilocali-4' in params:
				self.min_rooms = 4
			if '5-locali-o-piu' in params:
				self.min_rooms = 5
			if '5-locali-o-piu' not in params and 'quadrilocali-4' in params:
				self.max_rooms = 4
			if '5-locali-o-piu' not in params and 'quadrilocali-4' not in params and 'trilocali-3' in params:
				self.max_rooms = 3
			if '5-locali-o-piu' not in params and 'quadrilocali-4' not in params and 'trilocali-3' not in params \
				and 'bilocali-2' in params:
				self.max_rooms = 2
			if '5-locali-o-piu' not in params and 'quadrilocali-4' not in params and 'trilocali-3' not in params \
				and 'bilocali-2' not in params and 'monolocali-1' in params:
				self.max_rooms = 1
			if 'con-prezzo' in param:
				self.max_prize = param.split('_')[1] if len(param.split('_')) > 1 else None
			if 'prezzo-min' in param:
				self.min_prize = param.split('_')[1] if len(param.split('_')) > 1 else None
			if 'dimensione' in param:
				self.min_surface = param.split('_')[1] if len(param.split('_')) > 1 else None
			if 'dimensione-max' in param:
				self.max_surface = param.split('_')[1] if len(param.split('_')) > 1 else None
			if 'anunciante-particular' in param:
				self.agency_filter = True
			if 'aste-no' in param:
				self.auction_filter = True
			if 'piano-terra' in param:
				self.floor = FloorType.GROUND
			if 'piani-intermedi' in param:
				self.floor = FloorType.INTERMEDIATE
			if 'ultimo-piano' in param:
				self.floor = FloorType.LAST
			if 'piani-intermedi' in param and 'ultimo-piano' in param:
				self.floor = FloorType.INTERMEDIATELAST
			if 'piano-terra' in param and 'piani-intermedi' in param and 'ultimo-piano' in param:
				self.floor = FloorType.All

	def set_url(self):
		if self.source and self.city and self.type and self.category:
			category_type = 'vendita-case'
			if self.type == AdvType.AFFITTO and self.category == AdvCategory.IMMOBILE:
				category_type = 'affitto-case'
			elif self.type == AdvType.AFFITTO and self.category == AdvCategory.STANZA:
				category_type = 'affitto-stanze'
			elif self.type == AdvType.VENDITA and self.category == AdvCategory.NUOVACOSTRUZIONE:
				category_type = 'vendita-nuove_costruzioni'

			city = "-".join(format_text(self.city.lower()).split(" "))
			province = "-".join(format_text(self.province.lower()).split(" "))

			params = ""
			if self.min_rooms or self.max_rooms or self.min_prize or self.max_prize \
				or self.min_surface or self.max_surface or self.auction_filter or self.floor:
				params += "/con-"
				if self.max_prize:
					params += f"prezzo_{self.max_prize},"
				if self.min_prize:
					params += f"prezzo-min_{self.min_prize},"
				if self.floor == FloorType.GROUND:
					params += "piano-terra,"
				if self.floor == FloorType.INTERMEDIATE:
					params += "piani-intermedi,"
				if self.floor == FloorType.LAST:
					params += "ultimo-piano,"
				if self.category == AdvCategory.IMMOBILE:
					if self.min_surface:
						params += f"dimensione_{self.min_surface},"
					if self.max_surface:
						params += f"dimensione-max_{self.max_surface},"
					if (self.min_rooms or 0) <= 1 <= (self.max_rooms or math.inf):
						params += "monolocali-1,"
					if (self.min_rooms or 0) <= 2 <= (self.max_rooms or math.inf):
						params += "bilocali-2,"
					if (self.min_rooms or 0) <= 3 <= (self.max_rooms or math.inf):
						params += "trilocali-3,"
					if (self.min_rooms or 0) <= 4 <= (self.max_rooms or math.inf):
						params += "quadrilocali-4,"
					if (self.min_rooms or 0) <= 5 <= (self.max_rooms or math.inf):
						params += "5-locali-o-piu,"
					if self.auction_filter is True:
						params += "aste_no,"
				if self.category == AdvCategory.NUOVACOSTRUZIONE:
					if self.min_surface:
						params += f"dimensione_{self.min_surface},"
					if self.max_surface:
						params += f"dimensione-max_{self.max_surface},"
					if (self.min_rooms or 0) <= 1 <= (self.max_rooms or math.inf):
						params += "1-monolocali,"
					if (self.min_rooms or 0) <= 2 <= (self.max_rooms or math.inf):
						params += "2-bilocali,"
					if (self.min_rooms or 0) <= 3 <= (self.max_rooms or math.inf):
						params += "3-trilocali,"
					if (self.min_rooms or 0) <= 4 <= (self.max_rooms or math.inf):
						params += "4-quadrilocali,"
					if (self.min_rooms or 0) <= 5 <= (self.max_rooms or math.inf):
						params += "5-locali,"
				elif self.category == AdvCategory.STANZA:
					if self.agency_filter:
						params += "anunciante_particular,"
				if self.floor == FloorType.INTERMEDIATELAST:
					params += "piani-intermedi,ultimo-piano,"
			if params == "/con-":
				params = ""
			url = f"https://{self.source}/{category_type}/{city}-{province}{params}" \
				f"/?ordine=pubblicazione-desc"
			self.url = url
