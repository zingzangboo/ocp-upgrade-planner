"""
node.py
"""
import json
import logging
logger = logging.getLogger(__name__)
FIRST_RELEASE_VERSION = '4.1.0'


class Node:
    """
    A Node represents a particular version of OpenShift.
    """

    def __init__(self, node_json):
        self._json = node_json
        self._edges_to_me = set()
        self._edges_from_me = set()
        channel_names_string = self.metadata()[
            'io.openshift.upgrades.graph.release.channels'
        ]
        channel_names_array = channel_names_string.split(',')
        self._channel_names = set(channel_names_array)

    def __repr__(self):
        return f"Node({self.version()})"

    def metadata(self):
        """
        Return a dictionary containing metadata pertaining to the version
        of OpenShift represented by this Node.
        """
        return self._json['metadata']

    def version(self):
        """
        Return the version of OpenShift represented by this Node.
        """
        return self._json['version']

    def payload(self):
        """
        Return the image pull URL for the release image for the version of
        OpenShift represented by this Node.
        """
        return self._json['payload']

    def description(self):
        """
        Return the description of the OpenShift version represented by this
        Node, if there is one, or the empty string otherwise.
        At time of writing, almost all OpenShift versions had no description.
        """
        metadata = self.metadata()
        if 'description' in metadata:
            return metadata['description']
        # Not all nodes have description attributes
        logger.debug(
            "Node has no description: %s", json.dumps(self._json, indent=4)
        )
        return None

    def channel_names(self):
        """
        Return an array of the names of the channels that contain the
        OpenShift version represented by this Node.
        This information comes from an attribute of the Node in the API,
        so it duplicates the actual presence/absence of Nodes in Channels
        in the API, so inconsistencies are possible.
        """
        return self._channel_names

    def manifest(self):
        """
        Return the image digest for the release image for the version of
        OpenShift represented by this Node.
        """
        return self.metadata()[
            'io.openshift.upgrades.graph.release.manifestref'
        ]

    def url(self):
        """
        If the OpenShift version that this Node represents has a URL, return
        that URL.
        Otherwise, return None.
        When they are present, these URLs often refer to security advisories,
        presumably regarding bugs which are first fixed in that version.
        """
        metadata = self.metadata()
        if 'url' in metadata:
            return metadata['url']
        # Not all nodes have url attributes
        logger.debug(
            "Node has no url: %s",
            json.dumps(self._json, indent=4)
        )
        return None

    def add_edge(self, edge):
        """
        Add the given Edge into the set of Edges to or from this Node.
        """
        from_node = edge.from_node()
        to_node = edge.to_node()
        if from_node is self:
            self._edges_from_me.add(edge)
        elif to_node is self:
            self._edges_to_me.add(edge)
        else:
            raise ValueError("This edge has nothing to do with this node!")

    def edges_from(self):
        """
        Return the set of Edges that lead away from this Node,
        ie the set of all possible upgrade paths directly from the OpenShift
        version represented by this Node to other versions of OpenShift.
        """
        return self._edges_from_me

    def edges_to(self):
        """
        Return the set of Edges that lead to this Node,
        ie the set of all possible upgrade paths directly from some other
        OpenShift version to the OpenShift version represented by this Node.
        """
        return self._edges_to_me

    def assert_valid(self):
        """
        Assert that this Node is valid.
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
