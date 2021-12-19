import logging
import sys

from flask import Flask
from flask import request
from flask import jsonify

from statsbot.stats_bot import StatsBot

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=f'[%(asctime)s] [%(levelname)s] - %(message)s')
logger = logging.getLogger()
# logging.basicConfig(filename='stats_bot.log', level=logging.DEBUG, format=f'[%(asctime)s] [%(levelname)s] - %(message)s')

config = {}
with open("config.txt") as config_file:
    for line in config_file:
        name, value = line.partition("=")[::2]
        config[name.strip().lower()] = value.strip()
stats_bot = StatsBot(config)


@app.route("/")
def hello_world():
    logger.debug("Triggered Hello world page")
    return "<p>Hello, World!</p>"


@app.route('/stats', methods=['POST'])
def collect_stats():
    data = request.get_json()
    logger.debug("Received new stats request: %s", data)
    stats = stats_bot.run(data)
    logger.debug("Stats refreshed. Sending...")
    return jsonify(stats)
