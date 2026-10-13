"""
merged_catalog.py
"""
from version import Version


class MergedCatalog:
    """
    A MergedCatalog represents the merged/de-duplicated version of a Catalog,
    wherein all nodes and edges in all channels in the catalog have been
    merged into Versions and Upgrades.
    """

    def __init__(self, catalog):
        self._catalog = catalog
        self._build_merged_catalog()

    def _build_merged_catalog(self):
        """
        Build the set of merged nodes
        """
        self._version_to_node = {}
        for channel in self.catalog().channels():
            for node in channel.nodes():
                version = node.version()
                if version in self._version_to_node:
                    existing_merged_node = self._version_to_node[version]
                    existing_merged_node.merge_in_node(node)
                else:
                    new_merged_node = Version(node)
                    self._version_to_node[version] = new_merged_node
        for channel in self.catalog().channels():
            for node in channel.nodes():
                merged_node = self.get_merged_node_by_node(node)
                merged_node.merge_edges(self, node)

    def catalog(self):
        """
        Return the catalog that this MergedCatalog was created from.
        """
        return self._catalog

    def merged_nodes(self):
        """
        Return a list of all Versions in this MergedCatalog.
        """
        return self._version_to_node.values()

    def assert_valid(self):
        """
        Assert that this MergedCatalog is valid.
        """
        assert len(self.merged_nodes()) > 0
        for merged_node in self.merged_nodes():
            merged_node.assert_valid()

    def get_node_by_version(self, version):
        """
        Given an OpenShift version string, return the Version that
        represents that version in this MergedCatalog.
        """
        return self._version_to_node.get(version)

    def edges(self):
        """
        Enumerate all of the MergedEdges in this MergedCatalog.
        This represents every possible OpenShift upgrade path
        known to the catalog.
        """
        for merged_node in self.merged_nodes():
            yield from merged_node.edges_to()
            yield from merged_node.edges_from()

    def get_merged_node_by_node(self, node):
        """
        Given a Node representing an OpenShift version, return the Version
        that represents that version in this MergedCatalog.
        """
        merged_node = self.get_node_by_version(node.version())
        assert merged_node is not None
        return merged_node
