import os
import requests
import json
import logging

CACHE_DIR=os.getenv('TMPDIR', '/tmp')
API_URL='https://api.openshift.com/api/upgrades_info/v1/graph'
# TODO: There exist additional channel name prefixes, such as "eus" and "fast". Do we care about these?
# If these have different upgrade edges to "stable", we may need to query them to find the shortest upgrade path.
CHANNEL_NAME_PREFIXES=["stable"]
# OpenShift 3 is obsolete at time of writing
MAJOR_VERSION_MIN=4
# There was no OpenShift 4.0. The first release of OpenShift 4 was 4.1.
MINOR_VERSION_MIN=1
logger = logging.getLogger(__name__)

class CatalogCache:

    def __init__(self):
        pass

    @staticmethod
    # The pseudo-RESTful API returns 200 success and a particular reponse when a channel isn't found,
    # instead of accepting the version in the URL and returning 404 as a RESTful API would.
    # Recognise this special reponse.
    def _is_nonexistent_channel_response(response):
        if 200 != response.status_code:
            response.raise_for_status()
        payload = response.json()
        if "version" not in payload:
            raise(KeyError("No version in response"))
        if 1 != payload["version"]:
            raise(ValueError("Unrecognised response version '%s'" % payload["version"]))
        if "nodes" not in payload:
            raise(KeyError("No nodes in response %s" % json.dumps(payload)))
        if "edges" not in payload:
            raise(KeyError("No edges in response %s" % json.dumps(payload)))
        return len(payload["nodes"]) == 0 and len(payload["edges"]) == 0

    def _channels_in_major_version(self, channel_name_prefix, major_version):
        # The API seems not to provide a way to discover channels.
        # So we are forced to brute-force attack it in order to discover them :-(
        channels = []
        minor_version = MINOR_VERSION_MIN
        while (True):
            channel_name = "%s-%s.%s" % (channel_name_prefix, major_version, minor_version)
            logger.debug("Requesting '%s'" % channel_name)
            response = requests.get(
                API_URL,
                params={
                    'channel': channel_name
                }
            )
            if self._is_nonexistent_channel_response(response):
                return channels
            channels.append(channel_name)
            minor_version += 1

    def _get_uncached(self):
        # The API seems not to provide a way to discover channels.
        # So we are forced to brute-force attack it in order to discover them :-(
        channels = []
        for channel_name_prefix in CHANNEL_NAME_PREFIXES:
            major_version = MAJOR_VERSION_MIN
            channels_this_major_version = self._channels_in_major_version(channel_name_prefix, major_version)
            if len(channels_this_major_version):
                channels = channels + channels_this_major_version
            else:
                break
            major_version += 1
        return channels

    @staticmethod
    def _cache_filename():
        return "%s/catalog-cache" % (CACHE_DIR)

    def get_channel_names(self):
        cache_filename = self._cache_filename()
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
            ret = self._get_uncached()
            try:
                with open(cache_filename, "w") as cache_file:
                    cache_file.write(json.dumps(ret))
                logger.debug("Wrote cache %s" % cache_filename)
            except:
                logger.debug("Failed to write cache %s" % cache_filename)
        return ret
