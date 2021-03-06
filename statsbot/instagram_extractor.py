import json
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
        self.new_id_resolved = False
        self.name_to_id = {}
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

            self._load_id_file()
        except Exception as e:
            self.login_success = False
            error_message = str(e)

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

    def _load_id_file(self):
        self.name_to_id = {}
        if os.path.exists(os.path.join(Constants.CREDENTIALS_DIR, Constants.INSTAGRAM_ID_FILE)):
            with open(os.path.join(Constants.CREDENTIALS_DIR, Constants.INSTAGRAM_ID_FILE), 'r') as f:
                self.name_to_id = json.load(f)

    def _store_id_file(self):
        if self.new_id_resolved:
            with open(os.path.join(Constants.CREDENTIALS_DIR, Constants.INSTAGRAM_ID_FILE), 'w', encoding='utf-8') as f:
                json.dump(self.name_to_id, f, ensure_ascii=False, indent=4)
            self.new_id_resolved = False

    def is_working(self):
        return self.login_success

    def on_stop(self):
        self._store_id_file()

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
        user_id = self.name_to_id.get(user_name, "")
        if not user_id:
            user_id = self.instagrapi.user_id_from_username(user_name)
            self.name_to_id[user_name] = user_id
            self.new_id_resolved = True
            self.logger.debug("Instagram ID for user '%s' is resolved to %s", user_name, user_id)
        else:
            self.logger.debug("Instagram ID for user '%s' is already known: %s", user_name, user_id)

        user_info = self.instagrapi.user_info(user_id)

        last_n_days_post_count = 0
        last_n_days = datetime.datetime.now() - datetime.timedelta(days=Constants.LAST_N_DAYS)
        last_post_date = datetime.datetime.strptime("2000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")

        is_run = True
        if user_info.media_count == 0:
            self.logger.debug("No posts for Instagram user '%s'", user_name)
            last_post_date = ""
            is_run = False

        end_cursor = ""
        while is_run:
            posts, end_cursor = self.instagrapi.user_medias_paginated(int(user_id),
                                                                      Constants.SINGLE_REQUEST_POST_COUNT,
                                                                      end_cursor)
            if not posts:
                break

            self.logger.debug("Processing %d post(s) of Instagram user '%s'", len(posts), user_name)
            for post in posts:
                post_naive_date = post.taken_at.replace(tzinfo=None)
                if post_naive_date > last_post_date:
                    last_post_date = post_naive_date

                if post_naive_date >= last_n_days:
                    last_n_days_post_count += 1
                else:
                    is_run = False
                    break

        updated_user[Constants.INSTAGRAM_POST_COUNT] = user_info.media_count
        updated_user[Constants.INSTAGRAM_FOLLOWERS] = user_info.follower_count
        updated_user[Constants.INSTAGRAM_POST_LAST_N_DAYS_COUNT] = last_n_days_post_count
        updated_user[Constants.INSTAGRAM_POST_LAST_DATE] = str(last_post_date)

        self.logger.debug("Instagram user '%s' processed: followers %d, posts total %d, last %d days %d, last date %s",
                          user_name,
                          updated_user[Constants.INSTAGRAM_FOLLOWERS],
                          updated_user[Constants.INSTAGRAM_POST_COUNT],
                          Constants.LAST_N_DAYS,
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
