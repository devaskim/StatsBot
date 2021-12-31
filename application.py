from __future__ import print_function

import os.path
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from statsbot.constants import Constants
from statsbot.stats_bot import StatsBot


def init_logging():
    if not os.path.exists(Constants.LOGS_DIRECTORY):
        os.makedirs(Constants.LOGS_DIRECTORY)

    logger = logging.getLogger(Constants.LOGGER_NAME)
    logger.setLevel(Constants.LOG_LEVEL)
    handler = RotatingFileHandler(os.path.join(Constants.LOGS_DIRECTORY, Constants.LOG_FILE),
                                  maxBytes=Constants.LOG_MAX_FILE_SIZE,
                                  backupCount=Constants.LOG_MAX_FILE_COUNT)
    handler.setFormatter(logging.Formatter(f"[%(asctime)s] [%(levelname)s] - %(message)s"))
    handler.setLevel(Constants.LOG_LEVEL)
    logger.addHandler(handler)


def main():
    logger = logging.getLogger(Constants.LOGGER_NAME)

    if not os.path.exists(Constants.CREDENTIALS_DIR):
        os.makedirs(Constants.CREDENTIALS_DIR)

    creds = None
    if os.path.exists(os.path.join(Constants.CREDENTIALS_DIR, Constants.TOKEN_FILE)):
        creds = Credentials.from_authorized_user_file(os.path.join(Constants.CREDENTIALS_DIR, Constants.TOKEN_FILE),
                                                      Constants.SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(Constants.CREDENTIALS_DIR, Constants.CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(os.path.join(Constants.CREDENTIALS_DIR, Constants.TOKEN_FILE), 'w') as token:
            token.write(creds.to_json())

    app_config = {}
    with open(Constants.CONFIG_FILE) as file:
        for line in file:
            name, value = line.partition("=")[::2]
            app_config[name.strip().lower()] = value.strip()
    stats_bot = StatsBot(app_config)

    try:
        service = build('sheets', 'v4', credentials=creds)

        spreadsheets = service.spreadsheets()
        result = spreadsheets.values().get(spreadsheetId=app_config[Constants.CONFIG_SPREADSHEET_ID],
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
                if columns_number >= 5:
                    user[Constants.INSTAGRAM_POST_COUNT] = row[4]
                if columns_number >= 6:
                    user[Constants.INSTAGRAM_POST_LAST_N_DAYS_COUNT] = row[5]
                if columns_number >= 7:
                    user[Constants.INSTAGRAM_POST_LAST_DATE] = row[6]
                users.append(user)

        logger.info("%d user(s) will be processed", len(users))
        updated_users, last_run_timestamp = stats_bot.run(users)

        result = []
        for user in updated_users:
            result.append([user.get(Constants.SITE_TAG, ""),
                           "" if not user.get(Constants.SITE_TAG, "") else user.get(Constants.SITE_YEAR_TAG, -1),
                           user.get(Constants.INSTAGRAM_PAGE, ""),
                           user.get(Constants.INSTAGRAM_USER_ID, ""),
                           user.get(Constants.INSTAGRAM_POST_COUNT, ""),
                           user.get(Constants.INSTAGRAM_POST_LAST_N_DAYS_COUNT, ""),
                           user.get(Constants.INSTAGRAM_POST_LAST_DATE, "")])

        spreadsheets.values().update(spreadsheetId=app_config[Constants.CONFIG_SPREADSHEET_ID],
                                     range=app_config[Constants.CONFIG_SPREADSHEET_RANGE],
                                     valueInputOption="USER_ENTERED",
                                     body={"values": result}).execute()

        spreadsheets.batchUpdate(spreadsheetId=app_config[Constants.CONFIG_SPREADSHEET_ID],
                                 body={"requests": {
                                     "updateSpreadsheetProperties": {
                                         "properties": {
                                             "title": str(last_run_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                                         },
                                         "fields": "title"
                                     }
                                 }}).execute()

    except HttpError as err:
        logger.error("Failed to export data from Google Sheet")
        logger.error(err)


if __name__ == '__main__':
    init_logging()
    main()
