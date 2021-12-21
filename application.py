from __future__ import print_function

import os.path
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from statsbot.constants import Constants
from statsbot.stats_bot import StatsBot

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

LOG_LEVEL = logging.DEBUG
LOGS_DIRECTORY = "logs"
LOG_FILE = "app.log"
LOG_MAX_FILE_SIZE = 5 * 1024 * 1024
LOG_MAX_FILE_COUNT = 5

CONFIG_FILE = "config.txt"
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"


def init_logging():
    if not os.path.exists(LOGS_DIRECTORY):
        os.makedirs(LOGS_DIRECTORY)

    logger = logging.getLogger(Constants.LOGGER_NAME)
    logger.setLevel(LOG_LEVEL)
    handler = RotatingFileHandler(os.path.join(LOGS_DIRECTORY, LOG_FILE),
                                  maxBytes=LOG_MAX_FILE_SIZE,
                                  backupCount=LOG_MAX_FILE_COUNT)
    handler.setFormatter(logging.Formatter(f"[%(asctime)s] [%(levelname)s] - %(message)s"))
    handler.setLevel(LOG_LEVEL)
    logger.addHandler(handler)


def main():
    logger = logging.getLogger(Constants.LOGGER_NAME)

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    app_config = {}
    with open(CONFIG_FILE) as file:
        for line in file:
            name, value = line.partition("=")[::2]
            app_config[name.strip().lower()] = value.strip()
    stats_bot = StatsBot(app_config)

    try:
        service = build('sheets', 'v4', credentials=creds)

        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=app_config[Constants.CONFIG_SPREADSHEET_ID],
                                    range=app_config[Constants.CONFIG_SPREADSHEET_RANGE]).execute()
        values = result.get('values', [])

        if not values:
            logger.warning('No data received. Check Google Sheet content or application config')
            return

        users = []
        for row in values:
            columns_number = len(row)
            if columns_number >= 1:
                user = {Constants.SITE_TAG: row[0]}
                if columns_number >= 2:
                    user[Constants.SITE_YEAR_TAG] = row[1]
                if columns_number >= 3:
                    user[Constants.INSTAGRAM_PAGE] = row[2]
                if columns_number >= 4:
                    user[Constants.INSTAGRAM_USER_ID] = row[3]
                users.append(user)

        logger.info("%d user(s) will be processed", len(users))
        updated_users = stats_bot.run(users)

        result = []
        for user in updated_users:
            result.append([user.get(Constants.SITE_TAG, ""),
                           user.get(Constants.SITE_YEAR_TAG, -1),
                           user.get(Constants.INSTAGRAM_PAGE, ""),
                           user.get(Constants.INSTAGRAM_USER_ID, ""),
                           user.get(Constants.INSTAGRAM_POST_COUNT, 0),
                           user.get(Constants.INSTAGRAM_POST_LAST_MONTH_COUNT, 0),
                           user.get(Constants.INSTAGRAM_POST_LAST_DATE, "")])

        sheet.values().update(spreadsheetId=app_config[Constants.CONFIG_SPREADSHEET_ID],
                              range=app_config[Constants.CONFIG_SPREADSHEET_RANGE],
                              valueInputOption="USER_ENTERED",
                              body={"values": result}).execute()
    except HttpError as err:
        logger.error("Failed to export data from Google Sheet")
        logger.error(err)


if __name__ == '__main__':
    init_logging()
    main()
