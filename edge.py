class Edge:

    def __init__(self, from_node, to_node):
        self._from_node = from_node
        self._to_node = to_node

    def from_node(self):
        return self._from_node

    def to_node(self):
        return self._to_node
