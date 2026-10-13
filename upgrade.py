"""
upgrade.py
"""


class Upgrade:
    """
    A Upgrade represents a permitted direct upgrade from one particular
    version of OpenShift to another particular version of OpenShift.
    A particular direct upgrade can be present in multiple channels,
    so an Upgrade has a set of such Channels.
    """

    def __init__(self, channel, from_version, to_version):
        self._channels = set()
        self._channels.add(channel)
        self._from_version = from_version
        self._to_version = to_version
        self._risks = set()

    def __repr__(self):
        return (
            f"Upgrade({self.from_version().version()} -> "
            f"{self.to_version().version()}, channels={repr(self.channels())})"
        )

    def channels(self):
        """
        Return a set of the channels that this merged edge exists in.
        """
        return self._channels

    def channel_names(self):
        """
        Return the names of the channels that this merged edge exists in.
        """
        names = []
        for channel in self.channels():
            names.append(channel.name())
        return names

    def risks(self):
        """
        Return the set of Risks involved in this upgrade.
        """
        return self._risks

    def from_version(self):
        """
        Return the Version that represents the version of OpenShift
        prior to the upgrade that this Upgrade represents.
        """
        return self._from_version

    def to_version(self):
        """
        Return the Version that represents the version of OpenShift
        after the upgrade that this Upgrade represents.
        """
        return self._to_version

    def merge_in_edge(self, edge):
        """
        Merge the given Edge into this Upgrade.
        The edges' from and to versions must be consistent.
        The edges' set of channels need not be consistent.
        Instead, the Edge's set of channels will be added to this Upgrade's
        set of channels.
        """
        assert edge.from_node().version() == self.from_version().version()
        assert edge.to_node().version() == self.to_version().version()
        self._channels.add(edge.channel())
        self._risks.update(edge.risks())
