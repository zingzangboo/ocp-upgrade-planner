#!/usr/bin/python3

from sys import exit
from catalog import Catalog
import logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    catalog = Catalog()
    channel_names = catalog.channel_names()
    for channel_name in channel_names:
        channel = catalog.get_channel_by_name(channel_name)
        logger.debug(len(channel.nodes()))
        logger.debug(channel.nodes())
        break
    exit(0)
