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
            return []

        with self.lock:
            if self.in_progress:
                logger.info("Skip request for collecting stats: already in progress")
                return []
            self.in_progress = True

        self.worker = threading.Thread(target=self._run, args=(users,), daemon=True)
        self.worker.start()

    def _run(self, users):
        logger.info("Going to collect stats...")
        updated_users = []
        for user in users:
            for extractor in self.extractors:
                user = {**user, **extractor.get_stats(user)}
            updated_users.append(user)
        with self.lock:
            self.updated_users = updated_users
            self.in_progress = False
            self.last_run_timestamp = datetime.now()
        logger.info("Finished collecting stats")

    def get_stats(self):
        while self.lock:
            logger.info("Returning stats, cached at %s", self.last_run_timestamp)
            return self.updated_users

    def _read_input_data(self, file_in):
        users = []
        reader = csv.reader(file_in)
        for row in reader:
            user = {
                Constants.SITE_TAG: row[0],
                Constants.SITE_YEAR_TAG: row[1],
                Constants.INSTAGRAM_PAGE: row[2],
            }
            if len(row) > 3:
                user[Constants.INSTAGRAM_USER_ID] = row[3]
            users.append(user)
        return users

    def _write_output_data(self, file_out, users):
        with open(file_out, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=[Constants.SITE_TAG,
                                                          Constants.SITE_YEAR_TAG,
                                                          Constants.INSTAGRAM_PAGE,
                                                          Constants.INSTAGRAM_USER_ID,
                                                          Constants.INSTAGRAM_POST_COUNT,
                                                          Constants.INSTAGRAM_POST_LAST_MONTH_COUNT,
                                                          Constants.INSTAGRAM_POST_LAST_DATE])
            writer.writeheader()
            for user in users:
                writer.writerow(user)

