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
        return "MergedEdge(%s -> %s, channels=%s)" % (
            self.from_node().version(),
            self.to_node().version(),
            repr(self.channels())
        )

    def channels(self):
        return self._channels

    def from_node(self):
        return self._from_node

    def to_node(self):
        return self._to_node

    def merge_in_edge(self, other_edge):
        assert other_edge.from_node().version() == self.from_node().version()
        assert other_edge.to_node().version() == self.to_node().version()
        self._channels.add(other_edge.channel())
