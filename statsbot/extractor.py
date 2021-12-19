import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("extractor")


class Extractor(ABC):

    @abstractmethod
    def get_stats(self, user):
        pass
