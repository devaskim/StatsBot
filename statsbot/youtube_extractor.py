import datetime
import logging

import urllib.request, json

from statsbot.constants import Constants
from statsbot.extractor import Extractor


class YoutubeExtractor(Extractor):
    CHANNEL_INFO_ENDPOINT = "https://youtube.googleapis.com/youtube/v3/channels?part=statistics&id={0}&key={1}"
    CHANNEL_VIDEOS_ENDPOINT = "https://www.googleapis.com/youtube/v3/search?order=date&part=snippet&channelId={0}&maxResults={1}&key={2}"

    def __init__(self, config):
        self.logger = logging.getLogger(Constants.LOGGER_NAME)
        self.config = config

    def is_working(self):
        return True

    def on_stop(self):
        pass

    def get_stats(self, user):
        updated_user = {}
        if not self.is_working():
            self.logger.error("Skip collecting Youtube statistics: login failure")
            return updated_user

        if not user.get(Constants.YOUTUBE_PAGE, ""):
            return updated_user

        try:
            channel_id = self._extract_channel_id(user[Constants.YOUTUBE_PAGE])
            self.logger.debug("Requesting statistics for youtube channel, id: %s", channel_id)

            url = YoutubeExtractor.CHANNEL_INFO_ENDPOINT.format(channel_id, self.config[Constants.CONFIG_YOUTUBE_TOKEN])
            with urllib.request.urlopen(url) as request:
                response = json.loads(request.read().decode())

            youtube_statistics = response["items"][0]["statistics"]
            updated_user[Constants.YOUTUBE_POST_COUNT] = int(youtube_statistics["videoCount"])
            updated_user[Constants.YOUTUBE_FOLLOWERS] = int(youtube_statistics["subscriberCount"])
            updated_user[Constants.YOUTUBE_POST_LAST_N_DAYS_COUNT] = 0
            updated_user[Constants.YOUTUBE_POST_LAST_DATE] = ""

            if updated_user[Constants.YOUTUBE_POST_COUNT] == 0:
                self.logger.debug("No videos on youtube channel, id: %s", channel_id)
                return updated_user

            url = YoutubeExtractor.CHANNEL_VIDEOS_ENDPOINT.format(channel_id,
                                                                  Constants.SINGLE_REQUEST_POST_COUNT,
                                                                  self.config[Constants.CONFIG_YOUTUBE_TOKEN])
            with urllib.request.urlopen(url) as request:
                response = json.loads(request.read().decode())

            last_n_days_post_count = 0
            last_n_days = datetime.datetime.now() - datetime.timedelta(days=Constants.LAST_N_DAYS)

            for item in response["items"]:
                post_naive_date = datetime.datetime.strptime(item["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
                if post_naive_date >= last_n_days:
                    last_n_days_post_count += 1
                else:
                    break

            updated_user[Constants.YOUTUBE_POST_LAST_N_DAYS_COUNT] = last_n_days_post_count
            updated_user[Constants.YOUTUBE_POST_LAST_DATE] = str(response["items"][0]["snippet"]["publishedAt"])

            self.logger.debug("Youtube channel '%s' processed: followers %d, video total %d, last %d days %d, last date %s",
                              channel_id,
                              updated_user[Constants.YOUTUBE_FOLLOWERS],
                              updated_user[Constants.YOUTUBE_POST_COUNT],
                              Constants.LAST_N_DAYS,
                              updated_user[Constants.YOUTUBE_POST_LAST_N_DAYS_COUNT],
                              updated_user[Constants.YOUTUBE_POST_LAST_DATE])
        except Exception as e:
            self.logger.warning("Failed to collect stats for Youtube channel '%s'", channel_id)
            self.logger.warning(e)
        return updated_user

    def _extract_channel_id(self, url):
        if not url:
            return ""
        last_slash_pos = url.rfind("/")
        if last_slash_pos == len(url) - 1:
            return url[url.rfind("/", 0, last_slash_pos - 1) + 1: last_slash_pos]
        elif last_slash_pos > -1:
            return url[last_slash_pos + 1:]
        else:
            return url
