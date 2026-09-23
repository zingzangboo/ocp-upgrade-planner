import json
from node import Node
from edge import Edge

class Channel:

    def __init__(self, channel_name, json_data):
        self._name = channel_name
        self._json = json_data
        print(json.dumps(json_data))
        self._normalise_graph()

    def _normalise_graph(self):
        self._nodes = []
        for node_json in self._json['nodes']:
            self._nodes.append(Node(node_json))
        self._edges = []
        for edge in self._json['edges']:
            (from_node_index, to_node_index) = edge
            from_node = self._nodes[from_node_index]
            to_node = self._nodes[to_node_index]
            edge = Edge(from_node, to_node)
            self._edges.append(edge)
            from_node.add_edge(edge)
            to_node.add_edge(edge)
        self._nodes_by_version = dict()
        for node in self.nodes():
            self._nodes_by_version[node.version()] = node

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

    def risks(self):
        return self._json['risks']

    def condition_edges(self):
        return self._json['conditional_edges']
