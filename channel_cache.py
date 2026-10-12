"""
channel_cache.py
"""
import os
import json
import locale
import logging
import requests

CACHE_DIR = os.getenv('TMPDIR', '/tmp')
API_URL = 'https://api.openshift.com/api/upgrades_info/v1/graph'
logger = logging.getLogger(__name__)
"""
Timeout for accesses to the API in seconds.
"""
API_TIMEOUT = 3600


class ChannelCache:
    """
    A ChannelCache caches the data returned from the OpenShift API for
    individual Channels.
    """

    def __init__(self, architecture):
        self._architecture = architecture

    def architecture(self):
        """
        Return the microprocessor architecture associated with this Channel.
        """
        return self._architecture

    def _get_uncached(self, channel_name):
        """
        Fetch an API response, bypassing the client-side cache.
        """
        response = requests.get(
            API_URL, params={
                'channel': channel_name,
                'arch': self.architecture()
            },
            timeout=API_TIMEOUT
        )
        payload = response.json()
        return payload

    @staticmethod
    def _cache_filename(channel_name, architecture):
        """
        Given the name of a channel, return the filename to be used for
        caching API responses for that channel.
        """
        return (
            f"{CACHE_DIR}/ocpupgrade-channel-cache-"
            f"{channel_name}-{architecture}"
        )

    def get_channel_data(self, channel_name):
        """
        Given the name of a channel, return the API's details for that channel.
        This may be cached.
        """
        cache_filename = self._cache_filename(
            channel_name, self.architecture()
        )
        try:
            with open(
                cache_filename, "r", encoding=locale.getpreferredencoding(False)
            ) as cache_file:
                ret = json.load(cache_file)
            logger.debug("Read cache %s", cache_filename)
        except FileNotFoundError:
            logger.debug("No cache %s", cache_filename)
            ret = None
        except json.JSONDecodeError:
            logger.debug("Corrupt cache %s", cache_filename)
            ret = None
        if ret is None:
            ret = self._get_uncached(channel_name)
            try:
                with open(
                    cache_filename, "w", encoding=locale.getpreferredencoding(False)
                ) as cache_file:
                    cache_file.write(json.dumps(ret, indent=4))
                logger.debug("Wrote cache %s", cache_filename)
            except IOError:
                logger.warning("Failed to write cache %s", cache_filename)
        return ret
