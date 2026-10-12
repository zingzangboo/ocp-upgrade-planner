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
        self._channels_by_name = dict()
        for channel_name in self.channel_names():
            channel_json = self._channel_cache.get_channel_data(channel_name)
            channel = Channel(channel_name, channel_json)
            self._channels.append(channel)
            self._channels_by_name[channel.name()] = channel

    def architecture(self):
        return self._architecture

    def channel_names(self):
        return self._catalog_cache.get_channel_names()

    def get_channel_by_name(self, channel_name):
        return self._channels_by_name[channel_name]

    def channels(self):
        return self._channels

    def assert_valid(self):
        assert len(self.channels()) > 0
        for channel in self.channels():
            channel.assert_valid()
