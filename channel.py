"""
channel.py
"""
import logging
from node import Node
from edge import Edge
from risk import Risk
logger = logging.getLogger(__name__)


class Channel:
    """
    A Channel represents a set of available OpenShift versions and upgrade
    paths between them.
    Channel have names, which are of the following structure:
    1. A channel name prefix, currently "stable", "fast", "eus"
       or several other values;
    2. A "-" separator;
    3. An OpenShift major version number, such as "4";
    4. A "." separator;
    5. An OpenShift minor version number, such as "16".
    Each channel contains all OpenShift minor versions matching its name,
    and also all of the preceding minor versions, if any.
    For example, channel "stable-4.16" contains OpenShift versions 4.16.x
    (for all values of x), and also OpenShift versions 4.15.y (for all values
    of y).
    However channel "stable-4.1" contains OpenShift versions 4.1.x
    (for all values of x), but does not also contain any OpenShift
    versions 4.0.y (for any value of y), because those versions never existed,
    because the first release of OpenShift 4 had minor version 1, not 0.
    """
    def __init__(self, channel_name, json_data):
        self._name = channel_name
        self._json = json_data
        self._nodes = []
        self._edges = []
        self._nodes_by_version = {}
        self._normalise_graph()

    def __repr__(self):
        return f"Channel({self.name()})"

    def _add_nodes(self):
        """
        Build a list of all of the Nodes in this Channel.
        """
        for node_json in self._json['nodes']:
            self._nodes.append(Node(node_json))

    def _add_edges(self):
        """
        Build the Edges in this Channel.
        """
        for edge in self._json['edges']:
            (from_node_index, to_node_index) = edge
            from_node = self._nodes[from_node_index]
            to_node = self._nodes[to_node_index]
            edge = Edge(self, from_node, to_node)
            self._edges.append(edge)
            from_node.add_edge(edge)
            to_node.add_edge(edge)

    def _build_nodes_by_version(self):
        """
        Build a mapping from OpenShift versions to Edges.
        """
        for node in self.nodes():
            self._nodes_by_version[node.version()] = node

    def _merge_conditional_edges(self):
        """
        Merge the ConditionalEdges into the Edges.
        The only difference between Edges and ConditionalEdges seems to be
        that ConditionalEdges have risks and Edges don't.
        We can model this as an optional attribute 'risks'.
        By Occam's Razor, we shouldn't create a whole new entity.
        """
        for conditional_edge_json in self._json['conditionalEdges']:
            risks_json = conditional_edge_json['risks']
            edges_json = conditional_edge_json['edges']
            # We assume that Risk URLs uniquely define Risks
            risks = {}
            for risk_json in risks_json:
                risk_name = risk_json['name']
                risk_url = risk_json['url']
                risk_message = risk_json['message']
                risk = Risk(risk_name, risk_url, risk_message)
                if risk_url in risks:
                    raise ValueError("Duplicate Risks with URL {risk_url}")
                risks[risk_url] = risk
            for edge_json in edges_json:
                (from_version, to_version) = (
                    edge_json['from'], edge_json['to']
                )
                existing_edge = self.get_edge_by_versions(
                    from_version, to_version
                )
                if existing_edge:
                    # Add the new Risks to the existing Edge
                    existing_edge.add_risks(risks.values())
                else:
                    # Create a new Edge with the new Risks
                    from_node = self.get_node_by_version(from_version)
                    to_node = self.get_node_by_version(to_version)
                    new_edge = Edge(self, from_node, to_node, risks.values())
                    self._edges.append(new_edge)
                    from_node.add_edge(new_edge)
                    to_node.add_edge(new_edge)

    def _normalise_graph(self):
        self._add_nodes()
        self._add_edges()
        self._build_nodes_by_version()
        self._merge_conditional_edges()

    def get_node_by_version(self, version):
        """
        Given an OpenShift version string, return the Node in this Channel
        that represents that version of OpenShift.
        """
        return self._nodes_by_version[version]

    def name(self):
        """
        Return the name of this Channel.
        """
        return self._name

    def version(self):
        """
        Return the version of this channel.
        At time of writing, all channels had version 1, so it is not clear
        what this attribute means.
        """
        return self._json['version']

    def nodes(self):
        """
        Enumerate over all Nodes in this Channel.
        """
        return self._nodes

    def edges(self):
        """
        Enumerate over all Edges in this Channel.
        """
        return self._edges

    def get_edge_by_nodes(self, from_node, to_node):
        """
        Given two Nodes, find the Edge in this Channel that represents
        an upgrade of OpenShift from the first Node to the second Node.
        """
        for edge in self.edges():
            if edge.from_node() is from_node and edge.to_node() is to_node:
                return edge
        return None

    def get_edge_by_versions(self, from_version, to_version):
        """
        Given two OpenShift version strings, find the Edge in this Channel
        that represents an upgrade of OpenShift from the first version to
        the second version.
        """
        from_node = self.get_node_by_version(from_version)
        to_node = self.get_node_by_version(to_version)
        return self.get_edge_by_nodes(from_node, to_node)

    def risks(self):
        """
        Enumerate over all risks in this Channel.
        """
        return self._json['risks']

    def condition_edges(self):
        """
        Enumerate over all conditional edges in this Channel.
        """
        return self._json['conditional_edges']

    def assert_valid(self):
        """
        Assert that this Channel is valid.
        """
        assert len(self.nodes()) > 0
        for node in self.nodes():
            node.assert_valid()
