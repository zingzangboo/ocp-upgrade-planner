class Edge:
    """
    An Edge represents a permitted direct upgrade from one particular version
    of OpenShift to another particular version of OpenShift.
    It has a reference to the channel in which it was found.
    """

    def __init__(self, channel, from_node, to_node, risks=[]):
        self._channel = channel
        self._from_node = from_node
        self._to_node = to_node
        self._risks = risks

    def __repr__(self):
        return "Edge(%s -> %s)" % (
            self.from_node().version(), self.to_node().version()
        )

    def channel(self):
        return self._channel

    def from_node(self):
        return self._from_node

    def to_node(self):
        return self._to_node

    def risks(self):
        return self._risks

    def set_risks(self, risks):
        self._risks = risks
