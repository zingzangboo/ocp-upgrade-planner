from channel import Channel
from merged_node import MergedNode

class MergedCatalog:
    """
    A MergedCatalog represents the merged/de-duplicated version of a Catalog,
    wherein all nodes and edges in all channels in the catalog have been merged.
    """

    def __init__(self, catalog):
        self._catalog = catalog
        self._build_merged_catalog()

    def _build_merged_catalog(self):
        """Build the set of merged nodes"""
        self._version_to_node = dict()
        for channel in self.catalog().channels():
            for node in channel.nodes():
                version = node.version()
                if version in self._version_to_node:
                    existing_merged_node = self._version_to_node[version]
                    existing_merged_node.merge_in_node(node)
                else:
                    new_merged_node = MergedNode(node)
                    self._version_to_node[version] = new_merged_node
        for channel in self.catalog().channels():
            for node in channel.nodes():
                merged_node = self.get_merged_node_by_node(node)
                merged_node.merge_edges(self, node)

    def catalog(self):
        return self._catalog

    def merged_nodes(self):
        return self._version_to_node.values()

    def assert_valid(self):
        assert len(self.merged_nodes()) > 0
        for merged_node in self.merged_nodes():
            merged_node.assert_valid()

    def get_node_by_version(self, version):
        return self._version_to_node.get(version)

    def edges(self):
        for merged_node in self.merged_nodes():
            for edge in merged_node.edges_to():
                yield edge
            for edge in merged_node.edges_from():
                yield edge

    def get_merged_node_by_node(self, node):
        merged_node = self.get_node_by_version(node.version())
        assert merged_node is not None
        return merged_node
