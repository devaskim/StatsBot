import sys
import logging

from statsbot.stats_bot import StatsBot



def _init_logging():
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    log_format = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
    handler.setFormatter(log_format)

    logger.addHandler(handler)


def main():
    _init_logging()
    FILE_IN = 'stats_in.csv'
    FILE_OUT = 'stats_out.csv'
    bot = StatsBot()
    bot.run(FILE_IN, FILE_OUT)


if __name__ == '__main__':
    main()
