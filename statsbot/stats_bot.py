import csv
from datetime import datetime
import logging
import threading

from statsbot.who_is_extractor import WhoIsExtractor
from statsbot.instagram_extractor import InstagramExtractor
from statsbot.constants import Constants


logger = logging.getLogger("app.bot")


class StatsBot:

    def __init__(self, config):
        self.config = config
        self.extractors = [WhoIsExtractor(), InstagramExtractor(self.config)]
        self.updated_users = []
        self.last_run_timestamp = None;
        self.in_progress = False
        self.worker = None
        self.lock = threading.Lock()

    def run(self, users):
        if not isinstance(users, list) or not users:
            logger.warning("Skip collecting stats request: no incoming data")
            return []

        with self.lock:
            if self.in_progress:
                logger.info("Skip collecting stats request: already in progress")
                return []
            self.in_progress = True
            self.updated_users = []

        self.worker = threading.Thread(target=self._run, args=(users,), daemon=True)
        self.worker.start()

    def _run(self, users):
        logger.debug("Going to collect stats...")
        updated_users = []
        for user in users:
            for extractor in self.extractors:
                user = {**user, **extractor.get_stats(user)}
            updated_users.append(user)
        with self.lock:
            self.updated_users = updated_users
            self.in_progress = False
            self.last_run_timestamp = datetime.now()
        logger.info("Finished collecting stats at %s", self.last_run_timestamp)

    def get_stats(self):
        while self.lock:
            logger.info("Returning stats collected at %s", self.last_run_timestamp)
            return self.updated_users
