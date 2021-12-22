import logging
import time
from datetime import datetime

from statsbot.constants import Constants
from statsbot.extractor import Extractor

from instagrapi import Client


class InstagramExtractor(Extractor):
    UNKNOWN_USER_ID = 0

    def __init__(self, config):
        self.logger = logging.getLogger(Constants.LOGGER_NAME)
        self.instagrapi = Client()

        self.config = config
        if Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT not in self.config:
            self.logger.info("No request timeout configured for Instagram parser")
            self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT] = 0
        else:
            self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT] = int(
                self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT])
            self.logger.info("Request timeout for Instagram parser is configured to %d seconds",
                             self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT])

    def get_stats(self, user):
        try:
            return self.get_post_stats(user)
        except Exception as e:
            self.logger.warning("Failed to collect stats for Instagram user '%s'",
                                self._extract_username(user[Constants.INSTAGRAM_PAGE]))
            self.logger.warning(e)
        return {}

    def get_post_stats(self, user):
        updated_user = {}
        if not user.get(Constants.INSTAGRAM_PAGE, ""):
            return updated_user
        if self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT] > 0:
            self.logger.debug("Waiting for %d seconds before processing next Instagram user",
                              self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT])
            time.sleep(self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT])
        if not self.instagrapi.login(self.config[Constants.CONFIG_INSTAGRAM_USERNAME],
                                     self.config[Constants.CONFIG_INSTAGRAM_PASSWORD]):
            self.logger.error("Failed to login to Instagram")
            return updated_user
        user_name = self._extract_username(user[Constants.INSTAGRAM_PAGE])
        user_id = int(user.get(Constants.INSTAGRAM_USER_ID, InstagramExtractor.UNKNOWN_USER_ID))
        if user_id == InstagramExtractor.UNKNOWN_USER_ID:
            user_id = int(self.instagrapi.user_id_from_username(user_name))
            updated_user[Constants.INSTAGRAM_USER_ID] = user_id
            self.logger.debug("Instagram ID for user '%s' is resolved to %d", user_name, user_id)
        else:
            self.logger.debug("Instagram ID for user '%s' is already known: %d", user_name, user_id)

        posts = self.instagrapi.user_medias(user_id)
        if not posts:
            self.logger.debug("No posts for Instagram user '%s'", user_name)
            return {}

        now = datetime.now()
        last_month_pub_count = 0
        last_post_date = posts[0].taken_at
        self.logger.debug("Processing %d post(s) of Instagram user '%s'", len(posts), user_name)
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

        self.logger.debug("Instagram user '%s' processed: posts total %d, last month %d, last date %s",
                          user_name,
                          updated_user[Constants.INSTAGRAM_POST_COUNT],
                          updated_user[Constants.INSTAGRAM_POST_LAST_MONTH_COUNT],
                          updated_user[Constants.INSTAGRAM_POST_LAST_DATE])
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
