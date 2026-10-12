"""
catalog.py
"""
from catalog_cache import CatalogCache
from channel_cache import ChannelCache
from channel import Channel


class Catalog:
    """
    A Catalog represents a set of channels.
    """

    def __init__(self, architecture):
        self._architecture = architecture
        self._catalog_cache = CatalogCache(self.architecture())
        self._channel_cache = ChannelCache(self.architecture())
        self._channels = []
        self._channels_by_name = {}
        for channel_name in self.channel_names():
            channel_json = self._channel_cache.get_channel_data(channel_name)
            channel = Channel(channel_name, channel_json)
            self._channels.append(channel)
            self._channels_by_name[channel.name()] = channel

    def architecture(self):
        """
        Return the microprocessor architecture for this Channel.
        Each Channel is specific to a single such architecture.
        However, a given version of OpenShift may be present in multiple
        Channels, each for a different architecture.
        Consequently, a given version of OpenShift may not be specific to a
        single architecture.
        """
        return self._architecture

    def channel_names(self):
        """
        Return the names of this Channels in this Catalog.
        """
        return self._catalog_cache.get_channel_names()

    def get_channel_by_name(self, channel_name):
        """
        Given the name of a Channel in this Catalog,
        return the corresponding Channel.
        """
        return self._channels_by_name[channel_name]

    def channels(self):
        """
        Return a list of the Channels in this Catalog.
        """
        return self._channels

    def assert_valid(self):
        """
        Assert that this Catalog is valid.
        """
        assert len(self.channels()) > 0
        for channel in self.channels():
            channel.assert_valid()
