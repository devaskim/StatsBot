import logging
import sys
import os

from flask import Flask
from flask import request
from flask import jsonify

from statsbot.stats_bot import StatsBot

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1000 * 1000

LOGS_DIRECTORY = "logs"
LOG_FILE = "app.log"
CONFIG_FILE = "config.txt"

if not os.path.exists(LOGS_DIRECTORY):    
    os.makedirs(LOGS_DIRECTORY)

logging.basicConfig(filename=os.path.join(LOGS_DIRECTORY, LOG_FILE), level=logging.INFO, format=f"[%(asctime)s] [%(levelname)s] - %(message)s")
logger = logging.getLogger()

config = {}
with open(CONFIG_FILE) as file:
    for line in file:
        name, value = line.partition("=")[::2]
        config[name.strip().lower()] = value.strip()
stats_bot = StatsBot(config)


@app.route("/")
def hello_world():
    return "<h3>Greetings!</h3><p>Use <i>/stats</i> endpoint to get statistics or force it collecting.</p>"


@app.route("/stats", methods=["GET", "POST"])
def stats():
    if request.method == "GET":
        return jsonify(stats_bot.get_stats())
    else:
        data = request.get_json()
        logger.info("Received new stats request: %d data rows", len(data))
        stats_bot.run(data)
        return "[]"
