class ProcessModel:
    f_nodes = []
    f_flow_objects = []
    f_edges = []
    f_flows = []

    def get_successors(self, node):
        index = self.f_nodes.index(node)
        return self.f_nodes[:index]

    def get_predecessors(self, node):
        index = self.f_nodes.index(node)
        return self.f_nodes[index + 1:]

    def remove_node(self, node):
        if node in self.f_nodes:
            self.f_nodes.remove(node)

        if node in self.f_flow_objects:
            self.f_flow_objects.remove(node)

        for pnode in self.f_nodes:
            if isinstance(pnode, Cluster) and node in pnode.process_nodes:
                pnode.process_nodes.remove(node)

        for flow in self.f_flows:
            if flow.source == node or flow.target == node:
                self.f_flows.remove(flow)

        for edge in self.f_edges:
            if edge.source == node or edge.target == node:
                self.f_edges.remove(edge)


""" 
    Tree structure
    
    - SequenceFlow (edge)
    - FlowObject (node)
        - Activity
            - Task
        - Event
        - Gateway
    - Cluster
        - Lane
        - Pool
"""


class SequenceFlow:
    source = None
    target = None

    def __init__(self, source, target):
        self.source = source
        self.target = target


class FlowObject:
    text = ""


class Cluster:
    process_nodes = []
    name = None
    pool = None

    def __init__(self, name=None, pool=None):
        self.name = name
        self.pool = pool


class Lane(Cluster):
    pass


class Pool(Cluster):
    pass


class Event(FlowObject):
    parent_node = None
    class_type = None
    class_sub_type = None
    sub_type = None

    def __init__(self, event_type=None, sub_type=None):
        self.class_type = event_type
        self.class_sub_type = sub_type


class Gateway(FlowObject):
    type = None

    def __init__(self, gateway_type=None):
        self.type = gateway_type


class Activity(FlowObject):
    pass


class Task(Activity):
    pass
