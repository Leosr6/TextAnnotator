class ProcessModel:

    def __init__(self):
        self.nodes = []
        self.edges = []

    def get_successors(self, node):
        index = self.nodes.index(node)
        return self.nodes[:index]

    def get_predecessors(self, node):
        index = self.nodes.index(node)
        return self.nodes[index + 1:]

    def remove_node(self, node):
        if node in self.nodes:
            self.nodes.remove(node)

        for pnode in self.nodes:
            if isinstance(pnode, Cluster) and node in pnode.process_nodes:
                pnode.process_nodes.remove(node)

        for edge in self.edges:
            if edge.source == node or edge.target == node:
                self.edges.remove(edge)


""" 
    Tree structure
    
    - SequenceFlow (edge)
    - FlowObject (node)
        - Activity
        - Event
        - Gateway
    - Cluster
        - Lane
        - Pool
"""


class SequenceFlow:

    def __init__(self, source, target):
        self.source = source
        self.target = target


class FlowObject:

    def __init__(self):
        self.text = ""


class Cluster:

    def __init__(self, name=None, pool=None):
        self.process_nodes = []
        self.name = name
        self.pool = pool


class Lane(Cluster):
    pass


class Pool(Cluster):
    pass


class Event(FlowObject):

    def __init__(self, event_type=None, sub_type=None):
        super().__init__()
        self.class_type = event_type
        self.class_sub_type = sub_type
        self.parent_node = None
        self.sub_type = None


class Gateway(FlowObject):

    def __init__(self, gateway_type=None):
        super().__init__()
        self.type = gateway_type


class Activity(FlowObject):
    pass
