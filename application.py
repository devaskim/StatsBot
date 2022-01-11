from __future__ import print_function

import os.path
import logging
import os
from logging.handlers import RotatingFileHandler

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

from statsbot.constants import Constants
from statsbot.stats_bot import StatsBot


def init_logging():
    if not os.path.exists(Constants.LOGS_DIRECTORY):
        os.makedirs(Constants.LOGS_DIRECTORY)

    handler = RotatingFileHandler(os.path.join(Constants.LOGS_DIRECTORY, Constants.LOG_FILE),
                                  maxBytes=Constants.LOG_MAX_FILE_SIZE,
                                  backupCount=Constants.LOG_MAX_FILE_COUNT)
    handler.setFormatter(logging.Formatter(f"[%(asctime)s] [%(levelname)s] - %(message)s"))

    logger = logging.getLogger(Constants.LOGGER_NAME)
    logger.addHandler(handler)
    logger.setLevel(Constants.LOG_LEVEL)


def get_sheet_names(spreadsheet_service, spreadsheet_id):
    logger = logging.getLogger(Constants.LOGGER_NAME)
    result = []

    try:
        sheet_metadata = spreadsheet_service.get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        for sheet in sheets:
            title = sheet.get("properties", {}).get("title", "")
            if title:
                result.append(title)
        logger.debug("Sheet names: " + str(result))
    except Exception as e:
        logger.error("Failed to get sheet names: " + str(e))
    return result


def get_sheet_heading(spreadsheet_service, spreadsheet_id, sheet_name):
    result = spreadsheet_service.values().get(spreadsheetId=spreadsheet_id,
                                              range=sheet_name + "!1:1").execute()
    values = result.get('values', [])
    return values[0] if values else []


def filter_sheet(sheet_name, heading, filters):
    ranges = []
    keys = []
    sheet = {"ranges": [], "keys": []}
    for index, column_name in enumerate(heading):
        for f in filters:
            if column_name == f:
                column_letter = (chr(ord('a') + index)).upper()
                ranges.append(sheet_name + "!" + column_letter + "2:" + column_letter)
                keys.append(column_name)

    if len(filters) == len(keys):
        sheet["ranges"] = ranges
        sheet["keys"] = keys

    return sheet


def main():
    logger = logging.getLogger(Constants.LOGGER_NAME)

    if not os.path.exists(Constants.CREDENTIALS_DIR):
        os.makedirs(Constants.CREDENTIALS_DIR)

    try:
        app_config = {}
        with open(Constants.CONFIG_FILE) as file:
            for line in file:
                name, value = line.partition("=")[::2]
                app_config[name.strip().lower()] = value.strip()
        stats_bot = StatsBot(app_config)

        if os.path.exists(os.path.join(Constants.CREDENTIALS_DIR, Constants.TOKEN_FILE)):
            creds = Credentials.from_service_account_file(os.path.join(Constants.CREDENTIALS_DIR, Constants.TOKEN_FILE),
                                                          scopes=Constants.SPREADSHEET_SCOPES)
        else:
            logger.fatal("No Google service account in %s",
                         os.path.exists(os.path.join(Constants.CREDENTIALS_DIR, Constants.TOKEN_FILE)))
            return

        service = build('sheets', 'v4', credentials=creds)
        spreadsheets = service.spreadsheets()

        sheet_names = get_sheet_names(spreadsheets, app_config[Constants.CONFIG_SPREADSHEET_ID])
        for sheet_name in sheet_names:
            logger.debug("Processing sheet %s", sheet_name)
            sheet_heading = get_sheet_heading(spreadsheets, app_config[Constants.CONFIG_SPREADSHEET_ID], sheet_name)

            instagram_mapping = filter_sheet(sheet_name, sheet_heading, Constants.INSTAGRAM_FILTERS)
            whois_mapping = filter_sheet(sheet_name, sheet_heading, Constants.WHOIS_FILTERS)
            youtube_mapping = filter_sheet(sheet_name, sheet_heading, Constants.YOUTUBE_FILTERS)

            mapping = {"ranges": instagram_mapping["ranges"] + whois_mapping["ranges"] + youtube_mapping["ranges"],
                       "keys": instagram_mapping["keys"] + whois_mapping["keys"] + youtube_mapping["keys"]}
            if not mapping["ranges"]:
                logger.debug("No mapped columns in sheet %s", sheet_name)
                continue

            logger.debug("Exporting data from sheet %s, keys '%s'", sheet_name, str(mapping["keys"]))
            result = spreadsheets.values().batchGet(spreadsheetId=app_config[Constants.CONFIG_SPREADSHEET_ID],
                                                    ranges=mapping["ranges"],
                                                    majorDimension="COLUMNS").execute()
            values_ranges = result.get('valueRanges', [])
            if not values_ranges:
                logger.debug("No data has been exported from sheet %s", sheet_name)
                continue

            max_range_len = 0
            for value_range in values_ranges:
                range_len = len(value_range["values"][0]) if value_range.get("values", []) else 0
                if range_len > max_range_len:
                    max_range_len = range_len

            records = []
            for value_index in range(max_range_len):
                record = {}
                for key_index, key_value in enumerate(mapping["keys"]):
                    try:
                        record[key_value] = values_ranges[key_index]["values"][0][value_index]
                    except (IndexError, KeyError) as e:
                        record[key_value] = ""
                records.append(record)

            logger.info("%d record(s) will be processed from sheet %s", len(records), sheet_name)
            updated_records, last_run_timestamp = stats_bot.run(records)

            output_data = {"valueInputOption": "USER_ENTERED", "data": []}
            for key_index, key_value in enumerate(mapping["keys"]):
                output_range = {"range": mapping["ranges"][key_index],
                                "majorDimension": "COLUMNS"}
                output_range_values = []

                for record in updated_records:
                    output_range_values.append(record[key_value])

                output_range["values"] = [output_range_values]
                output_data["data"].append(output_range)

            logger.debug("Importing updated data to sheet %s", sheet_name)
            spreadsheets.values().batchUpdate(spreadsheetId=app_config[Constants.CONFIG_SPREADSHEET_ID],
                                              body=output_data).execute()

        date_str = str(last_run_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("Last run timestamp set to %s", date_str)
        # spreadsheets.batchUpdate(spreadsheetId=app_config[Constants.CONFIG_SPREADSHEET_ID],
        #                          body={"requests": {
        #                              "updateSpreadsheetProperties": {
        #                                  "properties": {
        #                                      "title": date_str
        #                                  },
        #                                  "fields": "title"
        #                              }
        #                          }}).execute()
    except Exception as e:
        logger.error("Unrecoverable execution error: " + str(e))
    finally:
        stats_bot.stop()


if __name__ == '__main__':
    init_logging()
    main()
