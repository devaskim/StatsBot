import logging


class Constants:
    SITE_TAG = "site"
    SITE_YEAR_TAG = "site_year"

    WHOIS_FILTERS = [SITE_TAG,
                     SITE_YEAR_TAG]

    INSTAGRAM_PAGE = "insta_page"
    INSTAGRAM_POST_COUNT = "insta_post_count"
    INSTAGRAM_FOLLOWERS = "insta_followers"
    INSTAGRAM_POST_LAST_N_DAYS_COUNT = "insta_30_days_count"
    INSTAGRAM_POST_LAST_DATE = "insta_last_post_date"

    INSTAGRAM_FILTERS = [INSTAGRAM_PAGE,
                         INSTAGRAM_POST_COUNT,
                         INSTAGRAM_FOLLOWERS,
                         INSTAGRAM_POST_LAST_N_DAYS_COUNT,
                         INSTAGRAM_POST_LAST_DATE]

    FACEBOOK_PAGE = "fb_page"
    FACEBOOK_POST_COUNT = "fb_post_count"
    FACEBOOK_FOLLOWERS = "fb_followers"
    FACEBOOK_POST_LAST_N_DAYS_COUNT = "fb_30_days_count"
    FACEBOOK_POST_LAST_DATE = "fb_last_post_date"

    FACEBOOK_FILTERS = [FACEBOOK_PAGE,
                        FACEBOOK_POST_COUNT,
                        FACEBOOK_FOLLOWERS,
                        FACEBOOK_POST_LAST_N_DAYS_COUNT,
                        FACEBOOK_POST_LAST_DATE]

    YOUTUBE_PAGE = "youtube_page"
    YOUTUBE_POST_COUNT = "youtube_video_count"
    YOUTUBE_FOLLOWERS = "youtube_followers"
    YOUTUBE_POST_LAST_N_DAYS_COUNT = "youtube_30_days_count"
    YOUTUBE_POST_LAST_DATE = "youtube_last_video_date"

    YOUTUBE_FILTERS = [YOUTUBE_PAGE,
                       YOUTUBE_POST_COUNT,
                       YOUTUBE_FOLLOWERS,
                       YOUTUBE_POST_LAST_N_DAYS_COUNT,
                       YOUTUBE_POST_LAST_DATE]

    LOG_LEVEL = logging.DEBUG
    LOG_MAX_FILE_SIZE = 5 * 1024 * 1024
    LOG_MAX_FILE_COUNT = 5
    LOG_FORMAT = f"[%(asctime)s] [%(levelname)s] - %(message)s"
    LOGS_DIRECTORY = "logs"
    LOG_FILE = "app.log"
    LOGGER_NAME = "StatsBot"

    SPREADSHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    CONFIG_FILE = "config.txt"
    CREDENTIALS_DIR = "credentials"
    CREDENTIALS_FILE = "credentials.json"
    TOKEN_FILE = "token.json"
    COOKIE_FILE = "facebook_cookies.json"

    CONFIG_INSTAGRAM_USERNAME = "instagram_username"
    CONFIG_INSTAGRAM_PASSWORD = "instagram_password"
    CONFIG_FACEBOOK_USERNAME = "facebook_username"
    CONFIG_FACEBOOK_PASSWORD = "facebook_password"
    CONFIG_INSTAGRAM_SLEEP_TIMEOUT = "instagram_sleep_timeout"
    CONFIG_SPREADSHEET_ID = "spreadsheet_id"
    CONFIG_YOUTUBE_TOKEN = "youtube_token"
    CONFIG_THREADPOOL_SIZE = "threadpool_size"
    CONFIG_RUN_IN_PARALLEL = "run_in_parallel"

    INSTAGRAM_USER_SESSION_FILE = "instagram_{0}.json"
    INSTAGRAM_ID_FILE = "instagram_user_to_id.json"

    LAST_N_DAYS = 30
    SINGLE_REQUEST_POST_COUNT = LAST_N_DAYS
    FACEBOOK_MAX_POSTS_PER_PAGE = 200


