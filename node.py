import json
import logging
logger = logging.getLogger(__name__)
FIRST_RELEASE_VERSION='4.1.0'

class Node:
    """
    A Node represents a particular version of OpenShift.
    """

    def __init__(self, node_json):
        self._json = node_json
        self._edges_to_me = set()
        self._edges_from_me = set()
        channel_name_array = self._json['metadata']['io.openshift.upgrades.graph.release.channels'].split(',')
        self._channel_names = set(channel_name_array)

    def __repr__(self):
        return "Node(%s)" % self.version()

    def version(self):
        return self._json['version']

    def payload(self):
        return self._json['payload']

    def description(self):
        metadata = self._json['metadata']
        if 'description' in metadata:
            return metadata['description']
        # Not all nodes have description attributes
        # logger.debug("Node has no description: %s" % json.dumps(self._json, indent=4))
        return None

    def channel_names(self):
        return self._channel_names

    def manifest(self):
        return self._json['metadata']['io.openshift.upgrades.graph.release.manifestref']

    def url(self):
        metadata = self._json['metadata']
        if 'url' in metadata:
            return metadata['url']
        # Not all nodes have url attributes
        # logger.debug("Node has no url: %s" % json.dumps(self._json, indent=4))
        return None

    def add_edge(self, edge):
        from_node = edge.from_node()
        to_node = edge.to_node()
        if from_node is self:
            self._edges_from_me.add(edge)
        elif to_node is self:
            self._edges_to_me.add(edge)
        else:
            raise(ValueError("This edge has nothing to do with this node!"))

    def edges_from(self):
        return self._edges_from_me

    def edges_to(self):
        return self._edges_to_me

    def assert_valid(self):
        # We would like to be able to assert this, but we can't, because the API claims there are no upgrade paths to some versions.
        # For example, at time of writing, there are no edges from any other version to version 4.1.10.
        # Presumable, a customer must have done a fresh install to reach such a version.
        # assert FIRST_RELEASE_VERSION == self.version() or len(self.edges_to()) > 0
        # We would like to be able to assert this, but we can't, because the API claims there are no upgrade paths from some versions.
        # For example, at time of writing, there are no edges from version 4.1.41 to any other version.
        # Presumable, if a customer is using such a version, they cannot upgrade and must reinstall.
        # assert len(self.edges_from()) > 0
        pass
