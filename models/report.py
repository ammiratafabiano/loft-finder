from datetime import datetime

from costants import WatchType


class Report:
    def __init__(self):
        self.starting_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.ads_sent = [0] * len(WatchType)
        self.last_update = [None] * len(WatchType)
