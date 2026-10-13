"""
graph.py
"""
from version import Version


class Graph:
    """
    A Graph represents the merged/de-duplicated version of a Catalog,
    wherein all nodes and edges in all channels in the catalog have been
    merged into Versions and Upgrades.
    """

    def __init__(self, catalog):
        self._catalog = catalog
        self._build_graph()

    def _build_graph(self):
        """
        Build the set of Versions
        """
        self._version_string_to_version = {}
        for channel in self.catalog().channels():
            for node in channel.nodes():
                version = node.version()
                if version in self._version_string_to_version:
                    existing_version = self._version_string_to_version[
                        version
                    ]
                    existing_version.merge_in_node(node)
                else:
                    new_version = Version(node)
                    self._version_string_to_version[version] = new_version
        for channel in self.catalog().channels():
            for node in channel.nodes():
                version = self.get_version_by_node(node)
                version.merge_edges(self, node)

    def catalog(self):
        """
        Return the catalog that this Graph was created from.
        """
        return self._catalog

    def versions(self):
        """
        Return a list of all Versions in this Graph.
        """
        return self._version_string_to_version.values()

    def assert_valid(self):
        """
        Assert that this Graph is valid.
        """
        assert len(self.versions()) > 0
        for version in self.versions():
            version.assert_valid()

    def get_version(self, version_string):
        """
        Given an OpenShift version string, return the Version that
        represents that version in this Graph.
        """
        return self._version_string_to_version.get(version_string)

    def upgrades(self):
        """
        Enumerate all of the Upgrades in this Graph.
        This represents every possible OpenShift upgrade path
        known to the catalog.
        """
        for version in self.versions():
            yield from version.upgrades_to()
            yield from version.upgrades_from()

    def get_version_by_node(self, node):
        """
        Given a Node representing an OpenShift version, return the Version
        that represents that version in this Graph.
        """
        version = self.get_version(node.version())
        assert version is not None
        return version
