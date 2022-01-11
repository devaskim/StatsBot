from datetime import datetime
import logging

from statsbot.constants import Constants
from statsbot.who_is_extractor import WhoIsExtractor
from statsbot.instagram_extractor import InstagramExtractor
from statsbot.youtube_extractor import YoutubeExtractor


class StatsBot:

    def __init__(self, config):
        self.logger = logging.getLogger(Constants.LOGGER_NAME)
        self.config = config
        self.extractors = [WhoIsExtractor(),
                           InstagramExtractor(self.config),
                           YoutubeExtractor(self.config)]
        self.updated_users = []
        self.last_run_timestamp = None

    def run(self, users):
        if not isinstance(users, list) or not users:
            self.logger.warning("Skip collecting stats request: no incoming data")
            return []
        updated_users = []
        for user in users:
            for extractor in self.extractors:
                if extractor.is_working():
                    user = {**user, **extractor.get_stats(user)}
            updated_users.append(user)
        self.last_run_timestamp = datetime.now()
        self.logger.info("Finished collecting stats at %s", self.last_run_timestamp)
        return updated_users, self.last_run_timestamp

    def stop(self):
        for extractor in self.extractors:
            extractor.on_stop()

    def get_stats(self):
        self.logger.info("Returning stats collected at %s", self.last_run_timestamp)
        return self.updated_users
