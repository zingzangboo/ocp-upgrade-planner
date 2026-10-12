import json
from node import Node
from edge import Edge


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
        self._normalise_graph()

    def __repr__(self):
        return "Channel(%s)" % self.name()

    def _normalise_graph(self):
        self._nodes = []
        for node_json in self._json['nodes']:
            self._nodes.append(Node(node_json))
        self._edges = []
        for edge in self._json['edges']:
            (from_node_index, to_node_index) = edge
            from_node = self._nodes[from_node_index]
            to_node = self._nodes[to_node_index]
            edge = Edge(self, from_node, to_node)
            self._edges.append(edge)
            from_node.add_edge(edge)
            to_node.add_edge(edge)
        self._nodes_by_version = dict()
        for node in self.nodes():
            self._nodes_by_version[node.version()] = node
        # Merge the conditionalEdges into the edges
        for conditional_edge_object in self._json['conditionalEdges']:
            cond_obj_edges = conditional_edge_object['edges']
            risks = conditional_edge_object['risks']
            # TODO: Factor out the risks into a separate list, instead of
            # copying them into each Edge.
            # Also, there may be duplication of the same risks across
            # different conditionalEdges/Channels/etc, which we should fix
            # by merging them.
            for cond_obj_edge in cond_obj_edges:
                (from_version, to_version) = (
                    cond_obj_edge['from'], cond_obj_edge['to']
                )
                existing_edge = self.get_edge_by_versions(
                    from_version, to_version
                )
                if existing_edge is None:
                    # An edge that is in conditionalEdges, but not in edges.
                    # Add it to edges with its risks.
                    new_edge = Edge(self, from_node, to_node, risks)
                    self._edges.append(new_edge)
                    from_node.add_edge(new_edge)
                    to_node.add_edge(new_edge)
                else:
                    # An edge in conditionalEdges that was already seen
                    # in edges. Add its risks to the existing edge.
                    existing_edge.set_risks(risks)

    def get_node_by_version(self, version):
        return self._nodes_by_version[version]

    def name(self):
        return self._name

    def version(self):
        return self._json['version']

    def nodes(self):
        return self._nodes

    def edges(self):
        return self._edges

    def get_edge_by_nodes(self, from_node, to_node):
        for edge in self.edges():
            if edge.from_node() is from_node and edge.to_node() is to_node:
                return edge

    def get_edge_by_versions(self, from_version, to_version):
        from_node = self.get_node_by_version(from_version)
        to_node = self.get_node_by_version(to_version)
        return self.get_edge_by_nodes(from_node, to_node)

    def risks(self):
        return self._json['risks']

    def condition_edges(self):
        return self._json['conditional_edges']

    def assert_valid(self):
        assert len(self.nodes()) > 0
        for node in self.nodes():
            node.assert_valid()
