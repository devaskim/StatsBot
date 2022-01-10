from abc import ABC, abstractmethod


class Extractor(ABC):

    @abstractmethod
    def get_stats(self, user):
        pass

    @abstractmethod
    def is_working(self):
        pass

    @abstractmethod
    def on_stop(self):
        pass
