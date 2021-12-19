import csv
import logging

from statsbot.who_is_extractor import WhoIsExtractor
from statsbot.instagram_extractor import InstagramExtractor
from statsbot.constants import Constants


logger = logging.getLogger("app.bot")


class StatsBot:

    def __init__(self, config):
        self.config = config
        self.extractors = [WhoIsExtractor(), InstagramExtractor(self.config)]

    def run(self, users):
        updated_users = []
        if not isinstance(users, list) or not users:
            return updated_users
        for user in users:
            for extractor in self.extractors:
                user = {**user, **extractor.get_stats(user)}
            updated_users.append(user)
        return updated_users

    def run_with_file(self, input_file):
        users = self._read_input_data(input_file)
        for extractor in self.extractors:
            users = extractor.get_stats(users)
        # self._write_output_data(file_out, users)

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

