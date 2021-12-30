import logging


class Constants:

    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    LOG_LEVEL = logging.DEBUG
    LOG_MAX_FILE_SIZE = 5 * 1024 * 1024
    LOG_MAX_FILE_COUNT = 5
    LOGS_DIRECTORY = "logs"
    LOG_FILE = "app.log"
    LOGGER_NAME = "StatsBot"

    CONFIG_FILE = "config.txt"
    CREDENTIALS_DIR = "credentials"
    CREDENTIALS_FILE = "credentials.json"
    TOKEN_FILE = "token.json"

    CONFIG_INSTAGRAM_USERNAME = "instagram_username"
    CONFIG_INSTAGRAM_PASSWORD = "instagram_password"
    CONFIG_INSTAGRAM_SLEEP_TIMEOUT = "instagram_sleep_timeout"
    CONFIG_SPREADSHEET_ID = "spreadsheet_id"
    CONFIG_SPREADSHEET_RANGE = "spreadsheet_range"

    SITE_TAG = "site"
    SITE_YEAR_TAG = "site_year"

    INSTAGRAM_PAGE = "insta_page"
    INSTAGRAM_USERNAME = "insta_name"
    INSTAGRAM_USER_ID = "insta_id"
    INSTAGRAM_POST_COUNT = "insta_post_count"
    INSTAGRAM_POST_LAST_N_DAYS_COUNT = "insta_last_month_post_count"
    INSTAGRAM_POST_LAST_DATE = "insta_last_post_date"

    INSTAGRAM_USER_SESSION_FILE = "instagram_{0}.json"

    INSTAGRAM_SINGLE_REQUEST_POST_COUNT = 10
    INSTAGRAM_SINGLE_REQUEST_MAX_POST_COUNT = 50
    INSTAGRAM_LAST_N_DAYS = 30




