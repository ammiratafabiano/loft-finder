import pickle
from datetime import datetime

from costants import WatchType
from models.report import Report
from models.user import User
from utils import format_name


class Storage:
	def __init__(self):
		self.users = []
		self.report = Report()
		self.load()
		self.load_report()

	def save(self):
		try:
			pickle.dump(self.users, open('storage.p', 'wb'))
			return self.users
		except (ValueError, Exception):
			return []

	def load(self):
		try:
			self.users = pickle.load(open('storage.p', 'rb'))
			return self.users
		except FileNotFoundError:
			return self.save()
		except (ValueError, Exception):
			return []

	def create_user(self, chat_id, username):
		self.load()
		new_user = User(chat_id, username)
		self.users.append(new_user)
		self.save()
		return new_user

	def retrieve_user(self, chat_id, username, first_name, last_name):
		self.load()
		for user in self.users:
			if user.chat_id == chat_id:
				# remove after fix all users
				if user.username is None:
					user.username = format_name(username, first_name, last_name)
					self.save()
				# end
				return user
		name = format_name(username, first_name, last_name)
		return self.create_user(chat_id, name)

	def delete_user(self, chat_id):
		for index, user in enumerate(self.users):
			if user.chat_id == chat_id:
				deleted = self.users.pop(index)
				self.save()
				return deleted
		return None

	def save_report(self):
		try:
			pickle.dump(self.report, open('report.p', 'wb'))
			return self.report
		except (ValueError, Exception):
			return Report()

	def load_report(self):
		try:
			self.report = pickle.load(open('report.p', 'rb'))
			return self.report
		except FileNotFoundError:
			return self.save_report()
		except (ValueError, Exception):
			return Report()

	def add_update(self, watch_type: str, ads_sent: int):
		if self.load_report():
			for i, watch_name in enumerate(WatchType):
				if watch_name.value == watch_type:
					self.report.last_update[i] = datetime.now().strftime("%d/%m/%Y %H:%M")
					self.report.ads_sent[i] += ads_sent
					self.save_report()
					return True
		else:
			return None

	def	restart_report(self):
		self.report = Report()
		self.save_report()


storage = Storage()
