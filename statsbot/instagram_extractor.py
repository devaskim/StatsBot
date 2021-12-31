import logging
import time
import os.path
import datetime

from statsbot.constants import Constants
from statsbot.extractor import Extractor

from instagrapi import Client


class InstagramExtractor(Extractor):

    def __init__(self, config):
        self.logger = logging.getLogger(Constants.LOGGER_NAME)
        self.config = config
        self.cred_file = os.path.join(Constants.CREDENTIALS_DIR,
                                      Constants.INSTAGRAM_USER_SESSION_FILE.format(
                                          self.config[Constants.CONFIG_INSTAGRAM_USERNAME]))

        error_message = ""
        try:
            self.instagrapi = Client()
            if os.path.exists(self.cred_file):
                self.instagrapi.load_settings(self.cred_file)
            self.login_success = self.instagrapi.login(self.config[Constants.CONFIG_INSTAGRAM_USERNAME],
                                                       self.config[Constants.CONFIG_INSTAGRAM_PASSWORD])
        except Exception as e:
            self.login_success = False
            error_message = e.message

        if not self.login_success:
            self.logger.error("Failed to login to Instagram: %s", error_message)
            return

        self.instagrapi.dump_settings(self.cred_file)

        if Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT not in self.config:
            self.logger.info("No request timeout configured for Instagram parser")
            self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT] = 0
        else:
            self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT] = int(
                self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT])
            self.logger.info("Request timeout for Instagram parser is configured to %d seconds",
                             self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT])

    def is_working(self):
        return self.login_success

    def get_stats(self, user):
        updated_user = {}
        if not self.is_working():
            self.logger.error("Skip collecting Instagram statistics: login failure")
            return updated_user

        try:
            updated_user = self.get_post_stats(user)
        except Exception as e:
            self.logger.warning("Failed to collect stats for Instagram user '%s'",
                                self._extract_username(user[Constants.INSTAGRAM_PAGE]))
            self.logger.warning(e)

        if user.get(Constants.INSTAGRAM_PAGE, "") and self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT] > 0:
            self.logger.debug("Waiting for %d seconds before processing next Instagram user",
                              self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT])
            time.sleep(self.config[Constants.CONFIG_INSTAGRAM_SLEEP_TIMEOUT])

        return updated_user

    def get_post_stats(self, user):
        updated_user = {}
        if not user.get(Constants.INSTAGRAM_PAGE, ""):
            return updated_user
        user_name = self._extract_username(user[Constants.INSTAGRAM_PAGE])
        user_id = user.get(Constants.INSTAGRAM_USER_ID, "")
        if not user_id:
            user_id = self.instagrapi.user_id_from_username(user_name)
            updated_user[Constants.INSTAGRAM_USER_ID] = user_id
            self.logger.debug("Instagram ID for user '%s' is resolved to %s", user_name, user_id)
        else:
            self.logger.debug("Instagram ID for user '%s' is already known: %s", user_name, user_id)

        last_n_days = datetime.datetime.now() - datetime.timedelta(days=Constants.INSTAGRAM_LAST_N_DAYS)

        last_n_days_post_count = 0
        total_post_count = user.get(Constants.INSTAGRAM_POST_COUNT, "")
        total_post_count = int(total_post_count) if total_post_count else 0
        is_first_time = total_post_count == 0

        last_post_date = user.get(Constants.INSTAGRAM_POST_LAST_DATE, "")
        if last_post_date:
            last_post_date = datetime.datetime.strptime(last_post_date, "%Y-%m-%d %H:%M:%S")
        else:
            last_post_date = datetime.datetime.strptime("2000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        previous_last_post_date = last_post_date

        if is_first_time:
            single_request_post_count = Constants.INSTAGRAM_SINGLE_REQUEST_MAX_POST_COUNT
        else:
            single_request_post_count = Constants.INSTAGRAM_SINGLE_REQUEST_POST_COUNT

        end_cursor = ""
        while True:
            posts, end_cursor = self.instagrapi.user_medias_paginated(int(user_id),
                                                                      single_request_post_count,
                                                                      end_cursor)
            if not posts:
                if total_post_count == 0:
                    self.logger.debug("No posts for Instagram user '%s'", user_name)
                    last_post_date = ""
                break

            self.logger.debug("Processing %d post(s) of Instagram user '%s'", len(posts), user_name)
            for post in posts:
                post_naive_date = post.taken_at.replace(tzinfo=None)
                if is_first_time or post_naive_date > previous_last_post_date:
                    total_post_count += 1

                if post_naive_date > last_post_date:
                    last_post_date = post_naive_date

                if post_naive_date >= last_n_days:
                    last_n_days_post_count += 1
                elif not is_first_time:
                    end_cursor = ""
                    break
            if not end_cursor:
                break

        updated_user[Constants.INSTAGRAM_POST_COUNT] = total_post_count
        updated_user[Constants.INSTAGRAM_POST_LAST_N_DAYS_COUNT] = last_n_days_post_count
        updated_user[Constants.INSTAGRAM_POST_LAST_DATE] = str(last_post_date)

        self.logger.debug("Instagram user '%s' processed: posts total %d, last %d days %d, last date %s",
                          user_name,
                          updated_user[Constants.INSTAGRAM_POST_COUNT],
                          Constants.INSTAGRAM_LAST_N_DAYS,
                          updated_user[Constants.INSTAGRAM_POST_LAST_N_DAYS_COUNT],
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
