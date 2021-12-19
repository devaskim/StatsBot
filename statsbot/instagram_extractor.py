import logging
from datetime import datetime

from statsbot.csv_constants import CSVConstants
from statsbot.extractor import Extractor, logger

from instagrapi import Client


logger = logging.getLogger("app.insta")


class InstagramExtractor(Extractor):
    ACCOUNT_USERNAME = 'devaskim'
    ACCOUNT_PASSWORD = 'Instagram.111989'

    def __init__(self, config):
        self.instagrapi = Client()
        self.config = config

    def get_stats(self, user):
        updated_user = {}
        if not self.instagrapi.login(self.config["insta_username"], self.config["insta_password"]):
            logger.error("Failed login to Instagram")
            return updated_user
        try:
            return self.get_post_stats(user)
        except Exception as e:
            logger.warning("Failed to collect stats for user: " + user[CSVConstants.INSTAGRAM_PAGE])
            logger.warning(e)
        return updated_user

    def get_post_stats(self, user):
        updated_user = {}
        if not user.get(CSVConstants.INSTAGRAM_PAGE):
            return updated_user
        if not user.get(CSVConstants.INSTAGRAM_USER_ID):
            user_name = self._extract_username(user[CSVConstants.INSTAGRAM_PAGE])
            updated_user[CSVConstants.INSTAGRAM_USER_ID] = self.instagrapi.user_id_from_username(user_name)

        posts = self.instagrapi.user_medias(updated_user[CSVConstants.INSTAGRAM_USER_ID])
        if not posts:
            return {}

        now = datetime.now()
        last_month_pub_count = 0
        last_post_date = posts[0].taken_at
        for post in posts:
            # YYYY-MM-DD
            if post.taken_at.month == now.month:
                last_month_pub_count += 1
            if post.taken_at > last_post_date:
                last_post_date = post.taken_at
        updated_user[CSVConstants.INSTAGRAM_POST_COUNT] = len(posts)
        updated_user[CSVConstants.INSTAGRAM_POST_LAST_DATE] = str(last_post_date.year) + "-" + \
                                                      str(last_post_date.month) + "-" + \
                                                      str(last_post_date.day)
        updated_user[CSVConstants.INSTAGRAM_POST_LAST_MONTH_COUNT] = last_month_pub_count

        return updated_user

    def _extract_username(self, username_in_page):
        if not username_in_page:
            return ""
        last_slash_pos = username_in_page.rfind("/")
        if last_slash_pos == len(username_in_page) - 1:
            return username_in_page[username_in_page.rfind("/", last_slash_pos - 1) + 1, last_slash_pos]
        elif last_slash_pos > -1:
            return username_in_page[last_slash_pos + 1:]
        else:
            return username_in_page
