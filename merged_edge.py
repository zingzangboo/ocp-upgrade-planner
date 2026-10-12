"""
merged_edge.py
"""


class MergedEdge:
    """
    A MergedEdge represents a permitted direct upgrade from one particular
    version of OpenShift to another particular version of OpenShift.
    A particular direct upgrade can be present in multiple channels,
    so a MergedEdge has a set of such channels.
    """

    def __init__(self, channel, from_node, to_node):
        self._channels = set()
        self._channels.add(channel)
        self._from_node = from_node
        self._to_node = to_node

    def __repr__(self):
        return (
            f"MergedEdge({self.from_node().version()} -> "
            f"{self.to_node().version()}, channels={repr(self.channels())})"
        )

    def channels(self):
        """
        Return a set of the channels that this merged edge exists in.
        """
        return self._channels

    def from_node(self):
        """
        Return the MergedNode that represents the version of OpenShift
        prior to the upgrade that this MergedEdge represents.
        """
        return self._from_node

    def to_node(self):
        """
        Return the MergedNode that represents the version of OpenShift
        after the upgrade that this MergedEdge represents.
        """
        return self._to_node

    def merge_in_edge(self, other_edge):
        """
        Merge the given Edge into this MergedEdge.
        The edges' from and to versions must be consistent.
        The edges' set of channels need not be consistent.
        Instead, the Edge's set of channels will be added to this MergedEdge's
        set of channels.
        """
        assert other_edge.from_node().version() == self.from_node().version()
        assert other_edge.to_node().version() == self.to_node().version()
        self._channels.add(other_edge.channel())
