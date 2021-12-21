from abc import ABC, abstractmethod


class Extractor(ABC):

    @abstractmethod
    def get_stats(self, user):
        pass
