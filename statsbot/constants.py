import logging

class Constants:
    SITE_TAG = "site"
    SITE_YEAR_TAG = "site_year"

    INSTAGRAM_PAGE = "insta_page"
    INSTAGRAM_USERNAME = "insta_name"
    INSTAGRAM_USER_ID = "insta_id"
    INSTAGRAM_POST_COUNT = "insta_post_count"
    INSTAGRAM_POST_LAST_MONTH_COUNT = "insta_last_month_post_count"
    INSTAGRAM_POST_LAST_DATE = "insta_last_post_date"

    CONFIG_INSTAGRAM_USERNAME = "instagram_username"
    CONFIG_INSTAGRAM_PASSWORD = "instagram_password"
    CONFIG_INSTAGRAM_SLEEP_TIMEOUT = "instagram_sleep_timeout"
    CONFIG_SPREADSHEET_ID = "spreadsheet_id"
    CONFIG_SPREADSHEET_RANGE = "spreadsheet_range"

    LOGGER_NAME = "StatsBot"
    LOG_LEVEL = logging.DEBUG
    LOGS_DIRECTORY = "logs"
    LOG_FILE = "app.log"
    LOG_MAX_FILE_SIZE = 5 * 1024 * 1024
    LOG_MAX_FILE_COUNT = 5

    CONFIG_FILE = "config.txt"

    CREDENTIALS_DIR = "credentials"
    CREDENTIALS_FILE = "credentials.json"
    TOKEN_FILE = "token.json"

    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']



