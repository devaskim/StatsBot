from datetime import datetime
import logging
import concurrent.futures

from statsbot.constants import Constants
from statsbot.who_is_extractor import WhoIsExtractor
from statsbot.instagram_extractor import InstagramExtractor
from statsbot.youtube_extractor import YoutubeExtractor
from statsbot.facebook_extractor import FacebookExtractor


class StatsBot:

    def __init__(self, config):
        self.logger = logging.getLogger(Constants.LOGGER_NAME)
        self.config = config
        self.updated_users = []
        self.last_run_timestamp = None
        self.logger.info("Statistics will have been collected in %s mode",
                         "parallel" if int(self.config[Constants.CONFIG_THREADPOOL_SIZE]) else "one-thread")
        self.extractors = [WhoIsExtractor(),
                           InstagramExtractor(self.config),
                           YoutubeExtractor(self.config),
                           FacebookExtractor(self.config)]

    def run(self, users):
        updated_users = []
        if not isinstance(users, list) or not users:
            self.logger.warning("Skip collecting stats request: no incoming data")
            return updated_users

        if int(self.config[Constants.CONFIG_RUN_IN_PARALLEL]):
            updated_users = self._run_in_parallel(users)
        else:
            updated_users = self._run(users)

        self.last_run_timestamp = datetime.now()
        self.logger.info("Finished collecting stats at %s", self.last_run_timestamp)
        return updated_users, self.last_run_timestamp

    def _run_in_parallel(self, users):
        updated_users = []
        futures = []
        with concurrent.futures.ThreadPoolExecutor(int(self.config[Constants.CONFIG_THREADPOOL_SIZE])) as pool:
            user_futures = []
            for user in users:
                for extractor in self.extractors:
                    if extractor.is_working():
                        user_futures.append(pool.submit(extractor.get_stats, user=user))
                futures.append(user_futures)

            for index, user_futures in enumerate(futures):
                user = users[index]
                for future in concurrent.futures.as_completed(user_futures):
                    user = {**user, **future.result()}
                updated_users.append(user)
        return updated_users

    def _run(self, users):
        updated_users = []
        for user in users:
            for extractor in self.extractors:
                if extractor.is_working():
                    user = {**user, **extractor.get_stats(user)}
            updated_users.append(user)
        return updated_users

    def stop(self):
        for extractor in self.extractors:
            extractor.on_stop()

    def get_stats(self):
        self.logger.info("Returning stats collected at %s", self.last_run_timestamp)
        return self.updated_users
