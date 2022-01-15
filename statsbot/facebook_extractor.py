import os
import logging
import datetime

from statsbot.constants import Constants
from statsbot.extractor import Extractor

from facebook_scraper import get_posts
from facebook_scraper import set_cookies
from facebook_scraper import get_page_info


class FacebookExtractor(Extractor):

    def __init__(self, config):
        self.logger = logging.getLogger(Constants.LOGGER_NAME)
        self.config = config
        set_cookies(os.path.join(Constants.CREDENTIALS_DIR, Constants.COOKIE_FILE))

    def get_stats(self, user):
        updated_user = {}
        if not self.is_working():
            self.logger.error("Skip collecting Facebook statistics: login failure")
            return updated_user

        if not user.get(Constants.FACEBOOK_PAGE, ""):
            return updated_user

        try:
            page_name = self._extract_page_name(user[Constants.FACEBOOK_PAGE])
            self.logger.debug("Requesting statistics for Facebook page, id: %s", page_name)

            page_info = get_page_info(page_name)
            updated_user[Constants.FACEBOOK_FOLLOWERS] = int(page_info["followers"])

            post_count = 0
            last_n_days_post_count = 0

            last_n_days = datetime.datetime.now() - datetime.timedelta(days=Constants.LAST_N_DAYS)
            last_post_date = datetime.datetime.strptime("2000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")

            credentials = [self.config[Constants.CONFIG_FACEBOOK_USERNAME],
                           self.config[Constants.CONFIG_FACEBOOK_PASSWORD]]
            options = {"allow_extra_requests": False,
                       "posts_per_page": Constants.FACEBOOK_MAX_POSTS_PER_PAGE}
            for post in get_posts(page_name, pages=None, options=options, credentials=credentials):
                post_count += 1
                if post['time'] > last_post_date:
                    last_post_date = post['time']
                if post['time'] > last_n_days:
                    last_n_days_post_count += 1

            updated_user[Constants.FACEBOOK_POST_COUNT] = post_count
            updated_user[Constants.FACEBOOK_POST_LAST_N_DAYS_COUNT] = last_n_days_post_count
            updated_user[Constants.FACEBOOK_POST_LAST_DATE] = str(last_post_date)

            self.logger.debug("Facebook page '%s' processed: followers %d, post total %d, last %d days %d, last date %s",
                              page_name,
                              updated_user[Constants.FACEBOOK_FOLLOWERS],
                              updated_user[Constants.FACEBOOK_POST_COUNT],
                              Constants.LAST_N_DAYS,
                              updated_user[Constants.FACEBOOK_POST_LAST_N_DAYS_COUNT],
                              updated_user[Constants.FACEBOOK_POST_LAST_DATE])
        except Exception as e:
            self.logger.warning("Failed to collect stats for Facebook page '%s'", page_name)
            self.logger.warning(e)
        return updated_user

    def _extract_page_name(self, url):
        if not url:
            return ""
        last_slash_pos = url.rfind("/")
        if last_slash_pos == len(url) - 1:
            return url[url.rfind("/", 0, last_slash_pos - 1) + 1: last_slash_pos]
        elif last_slash_pos > -1:
            return url[last_slash_pos + 1:]
        else:
            return url
