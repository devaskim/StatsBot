SHEET_TO_JSON_SERVICE = "https://opensheet.vercel.app/"

APP_HOST = "https://whispering-citadel-12723.herokuapp.com/"
APP_STATS_ENDPOINT = "stats"

WAIT_RESULT_TIMEOUT = 20000; // in miliseconds

function onOpen() {
  SpreadsheetApp.getUi()
                .createMenu("Статистика")
                .addItem("Обновить ", "refreshStatistics")
                .addToUi();
  // createTimeTrigger();
  updateSheetData(getCachedStatistics());
}

function createTimeTrigger() {
  ScriptApp.newTrigger("timeTrigger")
          .timeBased()
          .atHour(1)
          .everyDays(1)
          .create();
}

function refreshStatistics() {
  data = []
  forceCollecting();

  while (data.length === 0) {
    SpreadsheetApp.getActive().toast("Waiting " + WAIT_RESULT_TIMEOUT + " ms for updates", "⏰: In progress");
    Utilities.sleep(WAIT_RESULT_TIMEOUT);
    data = getCachedStatistics();
  }

  updateSheetData(data);
}

function timeTrigger() {
  refreshStatistics();
}

function forceCollecting() {
  var response = UrlFetchApp.fetch(SHEET_TO_JSON_SERVICE + SpreadsheetApp.getActiveSpreadsheet().getId() + "/1")
  if (response.getResponseCode() !== 200) {
    SpreadsheetApp.getActive().toast("Sheets to JSON service failed: response code " + response.getResponseCode() + "\n" +
                                 "Please, re-check your data and try again.", "⚠️ Warning");
    return;
  }

  SpreadsheetApp.getActive().toast("Sending request for statistics update...", " ⏰: Processing...");
  var options = {
    "method" : "post",
    "contentType": "application/json",
    "muteHttpExceptions": true,
    "payload" : response.getContentText()
  };
  response = UrlFetchApp.fetch(APP_HOST + "/" + APP_STATS_ENDPOINT, options)
  if (response.getResponseCode() !== 200) {
    SpreadsheetApp.getActive().toast("Failed to send data to refreshing statitsitcs: response code " + 
      response.getResponseCode() + "\n" + "Please, re-check your data and try again or see server logs", "⚠️ Error");
    return;
  }
}

function getCachedStatistics() {
  var options = {
    "method" : "get",
    "muteHttpExceptions": true,
  };

  response = UrlFetchApp.fetch(APP_HOST + "/" + APP_STATS_ENDPOINT, options)
  if (response.getResponseCode() !== 200) {
    SpreadsheetApp.getActive().toast("Failed to refresh stats: response code " + response.getResponseCode() + "\n" +
                                 "Please, re-check your data and try again.", "⚠️ Error");
    return [];
  }

  return JSON.parse(response.getContentText()); 
}

function updateSheetData(data) {
  if (data.length === 0) {
    return;
  }

  SpreadsheetApp.getActive().toast("Statistics received. Updating sheet...", "⏰: Processing...");
 
  var rows = [];
  for (i = 0; i < data.length; i++) {
    rows.push([data[i].site, 
               data[i].site_year,
               data[i].insta_page,
               data[i].insta_id,
               data[i].insta_post_count,
               data[i].insta_last_month_post_count,
               data[i].insta_last_post_date]);
  }

  dataRange = SpreadsheetApp.getActiveSpreadsheet()
                            .getActiveSheet()
                            .getRange(2, 1, rows.length, Object.keys(rows[0]).length);
  dataRange.setValues(rows);

  SpreadsheetApp.getActive().toast("Statistics refreshed", "👍 Success")
}
