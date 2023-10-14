from uuid import uuid4


class Adv:
	def __init__(self, display_name, url, prize):
		self.display_name = display_name
		self.url = url
		self.prize = prize


class Watch:
	def __init__(self, source):
		self.source = source
		self.display_name = ''
		self.description = ''
		self.url = None
		self.history = []
		self.uuid = uuid4().hex
		self.is_active = True
		self.status = True
		self.attempts = 0
		self.remaining_attempts = 0
		self.__set_filters()

	def get_ads(self):
		raise NotImplementedError('Please Implement this method')

	def __set_filters(self):
		self.city = None
		self.type = None
		self.category = None

	def set_url(self):
		self.url = None
