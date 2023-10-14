from costants import UrlWatchType, AdvType, FloorType, AdvCategory
from providers import *


class User:
	def __init__(self, chat_id: str, username: str):
		self.chat_id = chat_id
		self.username = username
		self.watchlist = []
		self.followers = []
		self.last_update = None

	def get_watch(self, url: str = None, uuid: str = None):
		if url or uuid:
			for watch in self.watchlist:
				if watch.url == url or watch.uuid == uuid:
					return watch
		return None

	def set_watch(self, watch):
		index = None
		for i, w in enumerate(self.watchlist):
			if w.uuid == watch.uuid:
				index = i
		if index is not None and index >= 0:
			self.watchlist[index] = watch
			return watch
		else:
			return None

	def add_watch(self, source: str, city: dict = None, adv_type: AdvType = None, adv_category: AdvCategory = None, agency_filter: bool = None,
		min_room: int = None, max_room: int = None, min_prize: int = None, max_prize: int = None, min_surface: int = None,
		max_surface: int = None, floor: FloorType = FloorType.ALL, description: str = None, url: str = None):
		if source == UrlWatchType.IMMOBILIARE.value:
			watch = ImmobiliareWatch(source, city, adv_type, adv_category, agency_filter, min_room, max_room, min_prize, max_prize,
				min_surface, max_surface, floor, description, url)
		elif source == UrlWatchType.SUBITO.value:
			watch = SubitoWatch(source, city, adv_type, adv_category, agency_filter, min_room, max_room, min_prize, max_prize,
				min_surface, max_surface, floor, description, url)
		elif source == UrlWatchType.CASADAPRIVATO.value:
			watch = CasaDaPrivatoWatch(source, city, adv_type, adv_category, min_room, max_room, min_prize, max_prize,
				min_surface, max_surface, description, url)
		elif source == UrlWatchType.CASA.value:
			watch = CasaWatch(source, city, adv_type, adv_category, agency_filter, min_room, max_room, min_prize, max_prize,
				min_surface, max_surface, floor, description, url)
		elif source == UrlWatchType.IDEALISTA.value:
			watch = IdealistaWatch(source, city, adv_type, adv_category, agency_filter, min_room, max_room, min_prize, max_prize,
				min_surface, max_surface, floor, description, url)
		else:
			watch = None

		self.watchlist.append(watch)
		return watch

	def remove_watch(self, uuid: str):
		for index, watch in enumerate(self.watchlist):
			if watch.uuid == uuid:
				return self.watchlist.pop(index)
		return None

	def suspend_watch(self, uuid: str):
		for watch in self.watchlist:
			if watch.uuid == uuid:
				watch.is_active = False
				return watch
		return None

	def resume_watch(self, uuid: str):
		for watch in self.watchlist:
			if watch.uuid == uuid:
				watch.is_active = True
				return watch
		return None

	def add_follower(self, chat_id):
		if hasattr(self, 'followers') and chat_id not in self.followers:
			self.followers.append(chat_id)
		else:
			self.followers = [chat_id]

	def remove_follower(self, chat_id):
		if hasattr(self, 'followers'):
			self.followers = []
			#self.followers.remove(chat_id)
