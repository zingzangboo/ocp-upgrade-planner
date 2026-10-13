"""
cincinnati_client.py
"""
import os
import json
import locale
import logging
import requests
from urllib3.exceptions import HTTPError as BaseHTTPError
from fopen import fopen

CACHE_DIR = os.getenv('TMPDIR', '/tmp')
CACHE_FILENAME_PREFIX = 'ocpupgrade-cache'
API_URL = 'https://api.openshift.com/api/upgrades_info/v1/graph'
# Do not fail CI merely because of an item needing fixing.
# pylint: disable=fixme
# TODO: Inspect all channels, in case there are different paths in different
# channels. Duplication opens up the possibility of self-contradiction.
# However, this would require downloading much additional channel data.
# Also, this would require a smarter version discovery algorithm, because
# although channels stable-4.{1..24} exist, only eus-4.6 and eus-4.{8..22}
# exist - eus-4.{1..5} and eus-4.7 do not exist.
# EUS versions are defined to have even release numbers, but apart from that,
# there seems to be no pattern here, so ugly hard-coding may be required :-(
# FIXME: The API seems to offer no way to discover these channel name prefixes,
# nor any easy way to discover which versions exist in which name prefixes.
# CHANNEL_NAME_PREFIXES = ["stable", "eus", "fast", "candidate"]
CHANNEL_NAME_PREFIXES = ["stable"]
# OpenShift 3 is obsolete at time of writing
MAJOR_VERSION_MIN = 4
# There was no OpenShift 4.0. The first release of OpenShift 4 was 4.1.
MINOR_VERSION_MIN = 1
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
"""
Timeout for accesses to the API in seconds.
"""
API_TIMEOUT = 3600


class NotFoundError(BaseHTTPError):
    """
    Represents an HTTP 404 error, thrown by the server when the URL supplied
    by the client does not locate an extant resource.
    """

    def __init__(self, msg):
        super().__init__(msg)


class CincinnatiClient:
    """
    A CincinnatiClient is a caching client for the OpenShift Cincinnati API.
    This API returns information about available OpenShift versions, upgrade
    paths between those versions, and risks during those upgrades.
    """

    def __init__(self, architecture):
        self._architecture = architecture

    def architecture(self):
        """
        Return this Catalog's processor achitecture.
        """
        return self._architecture

    @staticmethod
    # The pseudo-RESTful Cincinnati API returns 200 success and a particular
    # reponse when a channel isn't found, instead of accepting the version in
    # the URL and returning 404 as a RESTful API would.
    # Recognise this special reponse.
    # This is an example of an RPC-style, as opposed to RESTful, API.
    def _is_nonexistent_channel_response(response):
        payload = response.json()
        if "version" not in payload:
            raise KeyError(f"No version in response {json.dumps(payload)}")
        if 1 != payload["version"]:
            raise ValueError(
                f"Unrecognised response version '{payload['version']}'"
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

    def _get_single_channel_uncached(self, channel_name):
        """
        Fetch an API response, bypassing the client-side cache.
        """
        logger.debug("Downloading channel '%s'", channel_name)
        headers = {'Accept': 'application/json'}
        response = requests.get(
            API_URL,
            params={
                'channel': channel_name,
                'arch': self.architecture()
            },
            timeout=API_TIMEOUT,
            headers=headers
        )
        response.raise_for_status()
        if self._is_nonexistent_channel_response(response):
            # Convert the 200 success that the API returns on error to
            # an exception, to make sure the caller realises that
            # a failure has occurred.
            raise NotFoundError("No such channel %s" % channel_name)
        return response

    @staticmethod
    def _single_channel_cache_filename(channel_name, architecture):
        """
        Given the name of a channel, return the filename to be used for
        caching API responses for that channel.
        """
        return (
            f"{CACHE_DIR}/{CACHE_FILENAME_PREFIX}-channel-"
            f"{channel_name}-{architecture}"
        )

    def get_channel(self, channel_name):
        """
        Given the name of a channel, return the API's details for that channel.
        This may be cached.
        """
        cache_filename = self._single_channel_cache_filename(
            channel_name, self.architecture()
        )
        try:
            with fopen(cache_filename, "r") as cache_file:
                ret = json.load(cache_file)
            logger.debug("Read cache %s", cache_filename)
        except FileNotFoundError:
            logger.debug("No cache %s", cache_filename)
            ret = None
        except json.JSONDecodeError:
            logger.debug("Corrupt cache %s", cache_filename)
            ret = None
        if ret is None:
            response = self._get_single_channel_uncached(channel_name)
            ret = response.json()
            try:
                with open(
                    cache_filename, "w", encoding=locale.getpreferredencoding(False)
                ) as cache_file:
                    cache_file.write(json.dumps(ret, indent=4))
                logger.debug("Wrote cache %s", cache_filename)
            except IOError:
                logger.warning("Failed to write cache %s", cache_filename)
        return ret

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
            try:
                self.get_channel(channel_name)
            except NotFoundError:
                return channels
            channels.append(channel_name)
            minor_version += 1

    def _get_channel_names_uncached(self):
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
                next
            major_version += 1
        return channels

    @staticmethod
    def _cache_filename(architecture):
        return f"{CACHE_DIR}/{CACHE_FILENAME_PREFIX}-all-channel-names-{architecture}"

    def get_channel_names(self):
        """
        Enumerate the names of the Channels in this Catalog.
        """
        cache_filename = self._cache_filename(self.architecture())
        try:
            with fopen(cache_filename, "r") as cache_file:
                ret = json.load(cache_file)
            logger.debug("Read cache %s", cache_filename)
        except FileNotFoundError:
            logger.debug("No cache %s", cache_filename)
            ret = None
        except json.JSONDecodeError:
            logger.debug("Corrupt cache %s", cache_filename)
            ret = None
        if ret is None:
            ret = self._get_channel_names_uncached()
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
