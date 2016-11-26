#!/usr/bin/env python

import logging
import os

from beepboop import resourcer
from beepboop import bot_manager

from slack_bot import SlackBot
from slack_bot import spawn_bot

logger = logging.getLogger(__name__)


if __name__ == "__main__":

    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=log_level)

    slack_token = os.getenv("SLACK_TOKEN", "")
    logging.info("token: {}".format(slack_token))

    config_root = os.getenv("CONFIG_ROOT", "")
    logging.info("configuration root location: {}".format(config_root))
    
    host_config_root = os.getenv("HOST_CONFIG_ROOT", "")
    logging.info("host configuration root location: {}".format(host_config_root))
    
    if host_config_root == "":
        logging.info("HOST_CONFIG_ROOT env var not set. We can't proceed without it. It is the path _on the host_ to where VPN configuration folders live. It is used for starting containers that mount an individual subfolder as `/vpn`")
    if config_root == "":
        logging.info("CONFIG_ROOT env var not set. We can't proceed without it. It is the path _within the container_ to where VPN configuration folders live.")
    
    if slack_token == "":
        logging.info("SLACK_TOKEN env var not set, expecting token to be provided by Resourcer events")
        slack_token = None
        botManager = bot_manager.BotManager(spawn_bot)
        res = resourcer.Resourcer(botManager)
        res.start()
    else:
        # only want to run a single instance of the bot in dev mode
        bot = SlackBot(slack_token, host_config_root, config_root)
        bot.start({})
