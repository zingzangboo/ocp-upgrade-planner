"""
merged_node.py
"""
import logging
from merged_edge import MergedEdge
logger = logging.getLogger(__name__)
FIRST_RELEASE_VERSION = '4.1.0'


# It is not my fault that this entity has many attributes,
# and there is nothing I can do about it.
# pylint: disable=too-many-instance-attributes
class MergedNode:
    """
    A MergedNode represents a particular version of OpenShift.
    Any given OpenShift version can be present in multiple channels.
    This means that multiple semantically equivalent Node objects may
    be present in different Channel objects.
    Class MergedNode represents a unique OpenShift version, merged from
    the multiple Node objects referring to that version.
    While merging the duplicate nodes, we also check that they are consistent
    with each other.
    """

    def __init__(self, node):
        self._version = node.version()
        self._payload = node.payload()
        self._description = node.description()
        self._channel_names = node.channel_names()
        self._manifest = node.manifest()
        self._url = node.url()
        # These are maps from version to the MergedEdge object
        self._edges_to_me = {}
        self._edges_from_me = {}
        self.merge_in_node(node)

    def __repr__(self):
        return f"MergedNode({self.version()})"

    def version(self):
        """
        Return the version of OpenShift represented by this MergedNode.
        """
        return self._version

    def payload(self):
        """
        Return the image pull URL for the release image for the version of
        OpenShift represented by this MergedNode.
        """
        return self._payload

    def description(self):
        """
        Return the description of the OpenShift version represented by this
        MergedNode, if there is one, or the empty string otherwise.
        At time of writing, almost all OpenShift versions had no description.
        """
        return self._description

    def channel_names(self):
        """
        Return an array of the names of the channels that contain the
        OpenShift version represented by this MergedNode.
        This information comes from an attribute of the Node in the API,
        so it duplicates the actual presence/absence of Nodes in Channels
        in the API, so inconsistencies are possible.
        """
        return self._channel_names

    def manifest(self):
        """
        Return the image digest for the release image for the version of
        OpenShift represented by this MergedNode.
        """
        return self._manifest

    def url(self):
        """
        If the OpenShift version that this MergedNode represents has a URL,
        return that URL.
        Otherwise, return None.
        When they are present, these URLs often refer to security advisories,
        presumably regarding bugs which are first fixed in that version.
        """
        return self._url

    def merge_in_node(self, other_node):
        """
        Merge the information from the given Node into this MergedNode.
        Information that must be consistent is checked for consistency.
        Channel names are added, ie a setwise union is performed.
        """
        # Detect conflicting versions
        if other_node.version() != self.version():
            raise ValueError(
                f"Cannot merge node for version {other_node.version()} "
                f"into MergedNode for version {self.version()}"
            )
        # Detect conflicting payloads
        if other_node.payload() != self.payload():
            raise ValueError(
                f"Node for version {other_node.version()} has payload "
                f"{other_node.payload()}, but MergedNode for version "
                "{self.version()} has payload {self.payload()}"
            )
        # Detect conflicting descriptions
        if other_node.description() != self.description():
            raise ValueError(
                f"Node for version {other_node.version()} has description "
                f"{other_node.description()}, but MergedNode for version "
                f"{self.version()} has description {self.description()}"
            )
        # Merge channel names (which are expected to differ)
        self._channel_names.update(other_node.channel_names())
        # Detect conflicting manifests
        if other_node.manifest() != self.manifest():
            raise ValueError(
                f"Node for version {other_node.version()} has manifest "
                f"{other_node.manifest()}, but MergedNode for version "
                f"{self.version()} has manifest {self.manifest()}"
            )
        # Detect conflicting urls
        if other_node.url() != self.url():
            raise ValueError(
                f"Node for version {other_node.version()} has url "
                f"{other_node.url()}, "
                f"but MergedNode for version {self.version()} has url "
                f"{self.url()}"
            )

    def merge_edges(self, catalog, other_node):
        """
        Merge the set of Edges to/from the given Node into the set of
        MergedEdges to/from this MergedNode.
        """
        assert other_node.version() == self.version()
        self.merge_edges_to(catalog, other_node)
        self.merge_edges_from(catalog, other_node)

    def merge_edges_to(self, catalog, other_node):
        """
        Merge the set of Edges to the given Node into the set of
        MergedEdges to this MergedNode.
        """
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
                merged_from_node = catalog.get_merged_node_by_node(from_node)
                new_merged_edge = MergedEdge(channel, merged_from_node, self)
                self._edges_to_me[from_node_version] = new_merged_edge

    def merge_edges_from(self, catalog, other_node):
        """
        Merge the set of Edges from the given Node into the set of
        MergedEdges from this MergedNode.
        """
        assert other_node.version() == self.version()
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
                merged_to_node = catalog.get_merged_node_by_node(to_node)
                new_merged_edge = MergedEdge(channel, self, merged_to_node)
                self._edges_from_me[to_node_version] = new_merged_edge

    def edges_from(self):
        """
        Return the set of MergedEdges that lead away from this MergedNode,
        ie the set of all possible upgrade paths directly from the OpenShift
        version represented by this MergedNode to other versions of OpenShift.
        """
        return self._edges_from_me.values()

    def edges_to(self):
        """
        Return the set of MergedEdges that lead to this MergedNode,
        ie the set of all possible upgrade paths directly from some other
        OpenShift version to the OpenShift version represented by this
        MergedNode.
        """
        return self._edges_to_me.values()

    def get_edge_from_node(self, from_node):
        for edge in self.edges_to():
            assert edge.to_node() is self
            if edge.from_node() is from_node:
                return edge
        raise ValueError(
            f"No edge found from {repr(from_node)} to {repr(self)}"
        )

    def get_edge_to_node(self, to_node):
        for edge in self.edges_from():
            assert edge.from_node() is self
            if edge.to_node() is to_node:
                return edge
        raise ValueError(
            f"No edge found from {repr(self)} to {repr(to_node)}"
        )

    def assert_valid(self):
        """
        Assert that this MergedNode is valid.
        """
        # We would like to be able to assert this, but we can't, because the
        # API claims there are no upgrade paths to some versions.
        # For example, at time of writing, there are no edges from any other
        # version to version 4.1.10.
        # Presumable, a customer must have done a fresh install to reach such
        # a version.
        # assert (
        #     FIRST_RELEASE_VERSION == self.version() or
        #     len(self.edges_to()) > 0
        # )
        # We would like to be able to assert this, but we can't, because the
        # API claims there are no upgrade paths from some versions.
        # For example, at time of writing, there are no edges from version
        # 4.1.41 to any other version.
        # Presumable, if a customer is using such a version, they cannot
        # upgrade and must reinstall.
        # assert len(self.edges_from()) > 0
