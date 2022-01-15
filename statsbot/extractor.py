from abc import ABC, abstractmethod


class Extractor(ABC):

    @abstractmethod
    def get_stats(self, user):
        pass

    def is_working(self):
        return True

    def on_stop(self):
        pass
