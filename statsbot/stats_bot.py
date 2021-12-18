import csv
import logging

from statsbot.who_is_extractor import WhoIsExtractor
from statsbot.instagram_extractor import InstagramExtractor
from statsbot.csv_constants import CSVConstants


logger = logging.getLogger("app.bot")


class StatsBot:

    def __init__(self):
        self.extractors = [WhoIsExtractor(), InstagramExtractor()]

    def run(self, file_in, file_out):
        users = self._read_input_data(file_in)
        for extractor in self.extractors:
            users = extractor.get_stats(users)
        self._write_output_data(file_out, users)

    def _read_input_data(self, file_in):
        users = []
        with open(file_in) as csv_file_in:
            reader = csv.reader(csv_file_in)
            for row in reader:
                user = {
                    CSVConstants.SITE_TAG: row[0],
                    CSVConstants.SITE_YEAR_TAG: row[1],
                    CSVConstants.INSTAGRAM_PAGE: row[2],
                }
                if len(row) > 3:
                    user[CSVConstants.INSTAGRAM_USER_ID] = row[3]
                users.append(user)
        return users

    def _write_output_data(self, file_out, users):
        with open(file_out, 'w') as csvFile:
            writer = csv.DictWriter(csvFile, fieldnames=[CSVConstants.SITE_TAG,
                                                         CSVConstants.SITE_YEAR_TAG,
                                                         CSVConstants.INSTAGRAM_PAGE,
                                                         CSVConstants.INSTAGRAM_USER_ID,
                                                         CSVConstants.INSTAGRAM_POST_COUNT,
                                                         CSVConstants.INSTAGRAM_POST_LAST_MONTH_COUNT,
                                                         CSVConstants.INSTAGRAM_POST_LAST_DATE])
            writer.writeheader()
            for user in users:
                writer.writerow(user)

