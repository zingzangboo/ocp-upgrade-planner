class Node:

    def __init__(self, node_json):
        self._json = node_json
        self._edges_to_me = set()
        self._edges_from_me = set()

    def version(self):
        return self._json['version']

    def payload(self):
        return self._json['payload']

    def description(self):
        return self._json['metadata']['description']

    def channel_names(self):
        return self._json['metadata']['io.openshift.upgrades.graph.release.channels'].split(',')

    def manifest(self):
        return self._json['metadata']['io.openshift.upgrades.graph.release.manifestref']

    def url(self):
        return self._json['metadata']['url']

    def add_edge(self, edge):
        from_node = edge.from_node()
        to_node = edge.to_node()
        if from_node is self:
            self._edges_from_me.add(edge)
        elif to_node is self:
            self._edges_to_me.add(edge)
        else:
            raise(ValueError("This edge has nothing to do with me!"))

    def edges_from(self):
        return self._edges_from_me

    def edges_to(self):
        return self._edges_to_me
