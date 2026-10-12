"""
edge.py
"""

class Edge:
    """
    An Edge represents a permitted direct upgrade from one particular version
    of OpenShift to another particular version of OpenShift.
    It has a reference to the channel in which it was found.
    """

    def __init__(self, channel, from_node, to_node, risks=None):
        self._channel = channel
        self._from_node = from_node
        self._to_node = to_node
        self._risks = [] if risks is None else risks

    def __repr__(self):
        return (
            f"Edge({self.from_node().version()} -> {self.to_node().version()})"
        )

    def channel(self):
        """
        Return the Channel in which this Edge was found.
        """
        return self._channel

    def from_node(self):
        """
        Return the Node that represents the version of OpenShift
        prior to the upgrade that this Edge represents.
        """
        return self._from_node

    def to_node(self):
        """
        Return the Node that represents the version of OpenShift
        after the upgrade that this Edge represents.
        """
        return self._to_node

    def risks(self):
        """
        Return an array of risks associated with the OpenShift upgrade
        represented by this Edge.
        These "risks" can be anything, but are usually one of:
        - Step(s) which must be taken before the upgrade;
        - Step(s) which must be taken after the upgrade;
        - Circumstances in which this upgrade should not be attempted.
        """
        return self._risks

    def add_risks(self, risks):
        """
        Add the given array of risks to the set of risks associated with the
        OpenShift upgrade represented by this Edge.
        """
        assert self._risks is None
        self._risks = risks
