import os;
import json;
import requests;
import logging

CACHE_DIR=os.getenv('TMPDIR', '/tmp')
API_URL='https://api.openshift.com/api/upgrades_info/v1/graph'
logger = logging.getLogger(__name__)

class ChannelCache:

    def __init__(self):
        pass

    def _get_uncached(self, channel_name):
        response = requests.get(
            API_URL, params={
                'channel': channel_name
            }
        )
        payload = response.json()
        return payload

    @staticmethod
    def _cache_filename(channel_name):
        return "%s/channel-cache-%s" % (CACHE_DIR, channel_name)

    def get_channel_data(self, channel_name):
        cache_filename = self._cache_filename(channel_name)
        try:
            cache_file = open(cache_filename, "r")
            ret = json.load(cache_file)
            logger.debug("Read cache %s" % cache_filename)
        except FileNotFoundError:
            logger.debug("No cache %s" % cache_filename)
            ret = None
        except json.JSONDecodeError:
            logger.debug("Corrupt cache %s" % cache_filename)
            ret = None
        if ret is None:
            ret = self._get_uncached(channel_name)
            try:
                with open(cache_filename, "w") as cache_file:
                    cache_file.write(json.dumps(ret))
                logger.debug("Wrote cache %s" % cache_filename)
            except:
                logger.debug("Failed to write cache %s" % cache_filename)
        return ret
