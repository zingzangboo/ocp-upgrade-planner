from catalog_cache import CatalogCache
from channel_cache import ChannelCache
from channel import Channel

class Catalog:

    def __init__(self):
        self._catalog_cache = CatalogCache()
        self._channel_cache = ChannelCache()
        self._channels = []
        self._channels_by_name = dict()
        for channel_name in self.channel_names():
            channel_json = self._channel_cache.get_channel_data(channel_name)
            channel = Channel(channel_name, channel_json)
            self._channels.append(channel)
            self._channels_by_name[channel.name()] = channel

    def channel_names(self):
        return self._catalog_cache.get_channel_names()

    def get_channel_by_name(self, channel_name):
        return self._channels_by_name[channel_name]
    
    def channels(self):
        return self._channels
