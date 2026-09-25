from merged_edge import MergedEdge
import logging
logger = logging.getLogger(__name__)
FIRST_RELEASE_VERSION='4.1.0'

class MergedNode:
    """
    A MergedNode represents a particular version of OpenShift.
    Any given OpenShift version can be present in multiple channels.
    This means that multiple semantically equivalent Node objects may be present in different Channel objects.
    Class MergedNode represents a unique OpenShift version, merged from the multiple Node objects referring to that version.
    While merging the duplicate nodes, we also check that they are consistent with each other.
    """

    def __init__(self, node):
        self._version = node.version()
        self._payload = node.payload()
        self._description = node.description()
        self._channel_names = node.channel_names()
        self._manifest = node.manifest()
        self._url = node.url()
        # These are maps from version to the MergedEdge object
        self._edges_to_me = dict()
        self._edges_from_me = dict()
        if self.version() == "4.22.11":
            logger.debug("FOUND 4.22.11")
        self.merge_in_node(node)

    def __repr__(self):
        return "MergedNode(%s)" % self.version()

    def version(self):
        return self._version

    def payload(self):
        return self._payload

    def description(self):
        return self._description

    def channel_names(self):
        return self._channel_names

    def manifest(self):
        return self._manifest

    def url(self):
        return self._url

    def merge_in_node(self, other_node):
        # Detect conflicting versions
        if other_node.version() != self.version():
            raise(
                ValueError(
                    "Cannot merge node for version %s into MergedNode for version %s" %
                    (other_node.version(), self.version())
                )
            )
        # Detect conflicting payloads
        if other_node.payload() != self.payload():
            raise(
                ValueError(
                    "Node for version %s has payload %s, but MergedNode for version %s has payload %s" %
                    (other_node.version(), other_node.payload(), self.version(), self.payload())
                )
            )
        # Detect conflicting descriptions
        if other_node.description() != self.description():
            raise(
                ValueError(
                    "Node for version %s has description %s, but MergedNode for version %s has description %s" %
                    (other_node.version(), other_node.description(), self.version(), self.description())
                )
            )
        # Merge channel names (which are expected to differ)
        self._channel_names.update(other_node.channel_names())
        # Detect conflicting manifests
        if other_node.manifest() != self.manifest():
            raise(
                ValueError(
                    "Node for version %s has manifest %s, but MergedNode for version %s has manifest %s" %
                    (other_node.version(), other_node.manifest(), self.version(), self.manifest())
                )
            )
        # Detect conflicting urls
        if other_node.url() != self.url():
            raise(
                ValueError(
                    "Node for version %s has url %s, but MergedNode for version %s has url %s" %
                    (other_node.version(), other_node.url(), self.version(), self.url())
                )
            )
        # Merge edges (which are expected to differ)
        assert other_node.version() == self.version()
        for edge_to_me in other_node.edges_to():
            assert edge_to_me.to_node() is other_node
            assert edge_to_me.to_node().version() == self.version()
            from_node = edge_to_me.from_node()
            from_node_version = from_node.version()
            if from_node_version in self._edges_to_me:
                existing_merged_edge = self._edges_to_me[from_node_version]
                existing_merged_edge.merge_in_edge(edge_to_me)
            else:
                channel = edge_to_me.channel()
                new_merged_edge = MergedEdge(channel, from_node, self)
                self._edges_to_me[from_node_version] = new_merged_edge
        for edge_from_me in other_node.edges_from():
            assert edge_from_me.from_node() is other_node
            assert edge_from_me.from_node().version() == self.version()
            to_node = edge_from_me.to_node()
            to_node_version = to_node.version()
            if to_node_version in self._edges_from_me:
                existing_merged_edge = self._edges_from_me[to_node_version]
                existing_merged_edge.merge_in_edge(edge_from_me)
            else:
                channel = edge_from_me.channel()
                new_merged_edge = MergedEdge(channel, self, to_node)
                self._edges_from_me[to_node_version] = new_merged_edge

    def edges_from(self):
        return self._edges_from_me.values()

    def edges_to(self):
        return self._edges_to_me.values()

    def assert_valid(self):
        # We would like to be able to assert this, but we can't, because the API claims there are no upgrade paths to some versions.
        # For example, at time of writing, there are no edges from any other version to version 4.1.10.
        # Presumable, a customer must have done a fresh install to reach such a version.
        # assert FIRST_RELEASE_VERSION == self.version() or len(self.edges_to()) > 0
        # We would like to be able to assert this, but we can't, because the API claims there are no upgrade paths from some versions.
        # For example, at time of writing, there are no edges from version 4.2.0-0.hotfix-2020-09-19-234758 to any other version.
        # Presumable, if a customer is using such a version, they cannot upgrade and must reinstall.
        # assert len(self.edges_from()) > 0
        pass
