class ProcessModel:

    f_nodes = []
    f_flow_objects = []
    f_edges = []
    f_flows = []


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
