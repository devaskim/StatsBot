import logging
import time
from datetime import datetime

from statsbot.constants import Constants
from statsbot.extractor import Extractor

from instagrapi import Client


class InstagramExtractor(Extractor):
    def __init__(self, config):
        self.logger = logging.getLogger(Constants.LOGGER_NAME)
        self.instagrapi = Client()
        self.config = config

    def get_stats(self, user):
        try:
            time.sleep(int(self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT]))
            return self.get_post_stats(user)
        except Exception as e:
            self.logger.warning("Failed to collect stats for Instagram user '%s'",
                                    self._extract_username(user[Constants.INSTAGRAM_PAGE]))
            self.logger.warning(e)
        return {}

    def get_post_stats(self, user):
        updated_user = {}
        if not user.get(Constants.INSTAGRAM_PAGE, "") or not user.get(Constants.INSTAGRAM_USER_ID, ""):
            return updated_user
        if not self.instagrapi.login(self.config[Constants.CONFIG_INSTAGRAM_USERNAME],
                                     self.config[Constants.CONFIG_INSTAGRAM_PASSWORD]):
            self.logger.error("Failed to login to Instagram")
            return updated_user
        user_id = user.get(Constants.INSTAGRAM_USER_ID, "")
        if not user_id:
            user_name = self._extract_username(user[Constants.INSTAGRAM_PAGE])
            user_id = self.instagrapi.user_id_from_username(user_name)
            updated_user[Constants.INSTAGRAM_USER_ID] = user_id

        posts = self.instagrapi.user_medias(user_id)
        if not posts:
            return {}

        now = datetime.now()
        last_month_pub_count = 0
        last_post_date = posts[0].taken_at
        for post in posts:
            if post.taken_at.month == now.month:
                last_month_pub_count += 1
            if post.taken_at > last_post_date:
                last_post_date = post.taken_at
        updated_user[Constants.INSTAGRAM_POST_COUNT] = len(posts)
        updated_user[Constants.INSTAGRAM_POST_LAST_DATE] = str(last_post_date.year) + "-" + \
                                                           str(last_post_date.month) + "-" + \
                                                           str(last_post_date.day)
        updated_user[Constants.INSTAGRAM_POST_LAST_MONTH_COUNT] = last_month_pub_count

        return updated_user

    def _extract_username(self, username_in_page):
        if not username_in_page:
            return ""
        last_slash_pos = username_in_page.rfind("/")
        if last_slash_pos == len(username_in_page) - 1:
            return username_in_page[username_in_page.rfind("/", 0, last_slash_pos - 1) + 1: last_slash_pos]
        elif last_slash_pos > -1:
            return username_in_page[last_slash_pos + 1:]
        else:
            return username_in_page
