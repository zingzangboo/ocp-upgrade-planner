"""
catalog_cache.py
"""
import os
import json
import locale
import logging
import requests

CACHE_DIR = os.getenv('TMPDIR', '/tmp')
API_URL = 'https://api.openshift.com/api/upgrades_info/v1/graph'
# Inspect all channels, in case there are different paths in different
# channels.
# Do not fail CI merely because of an item needing fixing.
# pylint: disable=fixme
# FIXME: The API seems to offer no way to discover these channel name prefixes.
CHANNEL_NAME_PREFIXES = ["stable", "eus", "fast", "candidate"]
# OpenShift 3 is obsolete at time of writing
MAJOR_VERSION_MIN = 4
# There was no OpenShift 4.0. The first release of OpenShift 4 was 4.1.
MINOR_VERSION_MIN = 1
logger = logging.getLogger(__name__)
"""
Timeout for accesses to the API in seconds.
"""
API_TIMEOUT = 3600


class CatalogCache:
    """
    A CatalogCache caches the set of Channels returned by the OpenShift API.
    """

    def __init__(self, architecture):
        self._architecture = architecture

    def architecture(self):
        """
        Return this Catalog's processor achitecture.
        """
        return self._architecture

    @staticmethod
    # The pseudo-RESTful OpenShift API returns 200 success and a particular
    # reponse when a channel isn't found, instead of accepting the version in
    # the URL and returning 404 as a RESTful API would.
    # Recognise this special reponse.
    def _is_nonexistent_channel_response(response):
        if 200 != response.status_code:
            response.raise_for_status()
        payload = response.json()
        if "version" not in payload:
            raise KeyError("No version in response")
        if 1 != payload["version"]:
            raise ValueError(
                f"Unrecognised response version '{payload["version"]}'"
            )
        if "nodes" not in payload:
            raise KeyError(
                "No nodes in response {json.dumps(payload)}"
            )
        if "edges" not in payload:
            raise KeyError(
                "No edges in response {json.dumps(payload)}"
            )
        return len(payload["nodes"]) == 0 and len(payload["edges"]) == 0

    def _channels_in_major_version(self, channel_name_prefix, major_version):
        # The API seems not to provide a way to discover channels.
        # So we are forced to brute-force attack it in order to discover them
        # :-(
        channels = []
        minor_version = MINOR_VERSION_MIN
        while True:
            channel_name = (
                f"{channel_name_prefix}-{major_version}.{minor_version}"
            )
            logger.debug("Requesting '%s'", channel_name)
            response = requests.get(
                API_URL,
                params={
                    'channel': channel_name,
                    'arch': self.architecture()
                },
                timeout=API_TIMEOUT
            )
            if self._is_nonexistent_channel_response(response):
                return channels
            channels.append(channel_name)
            minor_version += 1

    def _get_uncached(self):
        # The API seems not to provide a way to discover channels.
        # So we are forced to brute-force attack it in order to discover them
        # :-(
        channels = []
        for channel_name_prefix in CHANNEL_NAME_PREFIXES:
            major_version = MAJOR_VERSION_MIN
            channels_this_major_version = self._channels_in_major_version(
                channel_name_prefix, major_version
            )
            if channels_this_major_version:
                channels = channels + channels_this_major_version
            else:
                break
            major_version += 1
        return channels

    @staticmethod
    def _cache_filename(architecture):
        return f"{CACHE_DIR}/ocpupgrade-catalog-cache-{architecture}"

    def get_channel_names(self):
        """
        Enumerate the names of the Channels in this Catalog.
        """
        cache_filename = self._cache_filename(self.architecture())
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
            ret = self._get_uncached()
            try:
                with open(
                    cache_filename, "w",
                    encoding=locale.getpreferredencoding(False)
                ) as cache_file:
                    cache_file.write(json.dumps(ret, indent=4))
                logger.debug("Wrote cache %s", cache_filename)
            except IOError:
                logger.warning("Failed to write cache %s", cache_filename)
        return ret
