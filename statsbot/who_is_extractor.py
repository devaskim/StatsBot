import re
import requests
import logging
from random import shuffle

from statsbot.constants import Constants
from statsbot.extractor import Extractor, logger

logger = logging.getLogger("app.whois")


class WhoIsExtractor(Extractor):
    UNKNOWN_YEAR = -1

    CREATION_DATE_SEARCH_TAG = "reat"
    CREATION_DATE_STRING_MAGIC_LENGTH = 50

    YEAR_REGEXP = re.compile(r"^.*(\d{4})[-,.]\d{2}[-,.]\d{2}.*$", re.MULTILINE)

    CONFIG = [{
        "whois": "https://www.whois.com/whois/",
        "tags": ["registryData", "registrarData"]
    }, {
        "whois": "https://www.whois.ru/",
        "tags": ["raw-domain-info-pre"]
    }, {
        "whois": "https://www.nic.ru/whois/?searchWord=",
        "tags": ["Whois-card"]
    }]

    HEADERS = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip,deflate",
        "Accept-Language": "en-US",
        "User-Agent": "Mozilla/5.0 (Macintosh Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (Kresponse.text, like Gecko) "
                      "Version/11.1.2 Safari/605.1.15"}

    def get_stats(self, user):
        updated_user = {}
        if not user.get(Constants.SITE_TAG):
            return updated_user
        if user.get(Constants.SITE_YEAR_TAG):
            return updated_user
        updated_user[Constants.SITE_YEAR_TAG] = self.get_creation_year(user[Constants.SITE_TAG])
        return updated_user

    def get_creation_year(self, url):
        domain = self._extract_domain(url)
        if not domain:
            logger.warning("Failed to get domain from %s'", url)
            return self.UNKNOWN_YEAR

        shuffle(self.CONFIG)

        for config in self.CONFIG:
            logger.debug("Requesting %s for domain %s", config["whois"], domain)

            # FIXME: maybe url must be encoded?
            response = requests.get(config["whois"] + domain, headers=self.HEADERS)
            if response.status_code != 200:
                return self.UNKNOWN_YEAR

            raw_data_position = 0
            for search_tag in config["tags"]:
                raw_data_position = response.text.find(search_tag)
                if raw_data_position > 0:
                    break

            if raw_data_position <= 0:
                logger.warning("Maybe captcha. Cannot find any search tag in %s for %s", config["whois"], domain)
                continue

            search_tag_position = response.text.find(self.CREATION_DATE_SEARCH_TAG, raw_data_position)
            while search_tag_position > -1:
                if response.text[search_tag_position - 1] == "c" or response.text[search_tag_position - 1] == "C":
                    test_string = response.text[search_tag_position: search_tag_position + self.CREATION_DATE_STRING_MAGIC_LENGTH]
                    match = re.search(self.YEAR_REGEXP, test_string)
                    if match:
                        year = int(match[1])
                        logger.debug("Resolve %d year for %s domain", year, domain)
                        return year

                search_tag_position = response.text.find(self.CREATION_DATE_SEARCH_TAG,
                                                         search_tag_position + len(self.CREATION_DATE_SEARCH_TAG))

            return self.UNKNOWN_YEAR

    def _extract_domain(self, url):
        domain = url
        if not domain:
            return ""
        http_pos = domain.find("http")
        if http_pos > -1:
            if domain.find("s://", 4) > 0:
                domain = domain[8:]
            elif domain.find("://", 4) > 0:
                domain = domain[7:]
        if domain.find("www.") > -1:
            domain = domain[4:]
        slash_pos = domain.find("/")
        if slash_pos > -1:
            domain = domain[0:slash_pos]

        logger.debug("Extract domain '%s' from '%s'", domain, url)

        return domain
