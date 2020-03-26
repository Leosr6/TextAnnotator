from core.WordNetWrapper import WordNetWrapper
from core.Base import Base
from utils import Processing
from utils.Constants import *
from data.BPMNElements import *
from data.SentenceElements import *
from data.TextElements import DummyAction


class ProcessModelBuilder(Base):

    f_world = None
    f_model = None
    f_flow_action_map = {}
    f_action_flow_map = {}
    f_actor_name_map = {}
    f_name_pool_map = {}
    f_main_pool = []
    f_not_assigned = []
    f_last_pool = None

    def __init__(self, world_model):
        self.f_world = world_model
        self.f_model = ProcessModel()

    def create_process_model(self):

        self.create_actions()
        self.build_sequence_flows()
        self.remove_dummies()
        self.finish_dangling_ends()
        self.process_meta_activities()

        # TODO: check if necessary
        # self.build_black_box_pools()
        # self.build_data_objects()

    def create_actions(self):
        for action in self.f_world.f_actions:
            if action.f_marker != IF and not action.f_markerFromPP:
                flow_object = self.create_task(action)
            else:
                flow_object = self.create_event_node(action)
                self.f_model.f_flow_objects.append(flow_object)
                flow_object.text = self.get_event_text(action) + " " + flow_object.text

            self.f_action_flow_map[action] = flow_object
            if action.f_xcomp:
                self.f_action_flow_map[action.f_xcomp] = flow_object
            self.f_flow_action_map[flow_object] = action

            lane = None
            if not WordNetWrapper.is_weak_action(action) and action.f_actorFrom:
                lane = self.get_lane(action.f_actorFrom)

            if not lane:
                if not self.f_last_pool:
                    self.f_not_assigned.append(flow_object)
                else:
                    self.f_last_pool.process_nodes.append(flow_object)
            else:
                lane.process_nodes.append(flow_object)
                for unass_object in self.f_not_assigned:
                    lane.process_nodes.append(unass_object)
                self.f_not_assigned.clear()
                self.f_last_pool = lane

    def build_sequence_flows(self):
        for flow in self.f_world.f_flows:
            if flow.f_type == SEQUENCE and len(flow.f_multiples) == 1:
                sequence_flow = SequenceFlow(self.to_process_node(flow.f_single),
                                             self.to_process_node(flow.f_multiples[0]))
                self.f_model.f_edges.append(sequence_flow)
            elif flow.f_type == EXCEPTION:
                exception_event = Event(INTERMEDIATE_EVENT, ERROR_EVENT)
                self.f_model.f_flow_objects.append(exception_event)
                task = self.to_process_node(flow.f_single)
                exception_event.parent_node = task
                self.add_to_same_lane(task, exception_event)

                sequence_flow = SequenceFlow(exception_event,
                                             self.to_process_node(flow.f_multiples[0]))
                self.f_model.f_edges.append(sequence_flow)
            elif flow.f_direction == SPLIT:
                gateway = self.create_gateway(flow)
                sequence_flow = SequenceFlow(self.to_process_node(flow.f_single), gateway)
                self.f_model.f_edges.append(sequence_flow)
                self.add_to_prevalent_lane(flow, gateway)
                for action in flow.f_multiples:
                    internal_flow = SequenceFlow(gateway, self.to_process_node(action))
                    self.f_model.f_edges.append(internal_flow)
            elif flow.f_direction == JOIN:
                gateway = self.create_gateway(flow)
                sequence_flow = SequenceFlow(gateway, self.to_process_node(flow.f_single))
                self.f_model.f_edges.append(sequence_flow)
                self.add_to_prevalent_lane(flow, gateway)
                for action in flow.f_multiples:
                    internal_flow = SequenceFlow(self.to_process_node(action), gateway)
                    self.f_model.f_edges.append(internal_flow)

    def remove_dummies(self):
        for action in self.f_world.f_actions:
            if isinstance(action, DummyAction) or action.f_transient or self.f_action_flow_map[action].text == DUMMY_NODE:
                self.remove_node(self.to_process_node(action))

    def finish_dangling_ends(self):
        source_map = {}
        target_map = {}

        # Calculating the occurrences of each node as a source and as a target
        for edge in self.f_model.f_edges:
            source_map[edge.source] = source_map.get(edge.source, 0) + 1
            target_map[edge.target] = target_map.get(edge.target, 0) + 1

        for node in self.f_model.f_nodes:
            if isinstance(node, Task) or isinstance(node, Gateway) or (isinstance(node, Event) and node.class_type == INTERMEDIATE_EVENT):
                # If the node is not present, add it with 0 occurrences
                source_map.setdefault(node, 0)
                target_map.setdefault(node, 0)

                if target_map[node] == 0 or (isinstance(node, Gateway) and source_map[node] == 1 and target_map[node] == 1):
                    end_event = Event(END_EVENT)
                    self.f_model.f_nodes.append(end_event)
                    self.add_to_same_lane(node, end_event)
                    sequence_flow = SequenceFlow(node, end_event)
                    self.f_model.f_flows.append(sequence_flow)
                if source_map[node] == 0:
                    if isinstance(node, Event) and node.class_type == INTERMEDIATE_EVENT and node.parent_node:
                        continue
                    else:
                        start_event = Event(START_EVENT)
                        self.f_model.f_nodes.append(start_event)
                        self.add_to_same_lane(node, start_event)
                        sequence_flow = SequenceFlow(start_event, node)
                        self.f_model.f_flows.append(sequence_flow)

    def process_meta_activities(self):
        for action in self.f_world.f_actions:
            if action.f_actorFrom and action.f_actorFrom.f_metaActor:
                if WordNetWrapper.is_verb_of_type(action.f_name, END_VERB):
                    node = self.f_action_flow_map[action]
                    successors = self.f_model.get_successors(node)
                    self.remove_node(node)
                    if action.f_name == TERMINATE and len(successors) == 1:
                        end_event = Event(END_EVENT)
                        Processing.refactor_node(self.f_model, end_event, TERMINATE_EVENT)
                elif WordNetWrapper.is_verb_of_type(action.f_name, START_VERB):
                    node = self.f_action_flow_map[action]
                    predecessors = self.f_model.get_predecessors(node)
                    if len(predecessors) == 1 and isinstance(predecessors[0], Event) and predecessors[0].type == START_EVENT:
                        self.remove_node(node)

    def create_task(self, action):
        task = Task()
        name = self.create_task_text(action)
        task.text = name
        self.f_model.f_flow_objects.append(task)
        return task

    def create_task_text(self, action):
        pass

    @staticmethod
    def create_event_node(action):
        for spec in action.f_specifiers:
            for word in spec.f_name.split(" "):
                if WordNetWrapper.is_time_period(word):
                    timer_event = Event(INTERMEDIATE_EVENT, TIMER_EVENT)
                    timer_event.text = spec.f_name
                    return timer_event

        if WordNetWrapper.is_verb_of_type(action.f_name, SEND) or WordNetWrapper.is_verb_of_type(action.f_name, RECEIVE):
            message_event = Event(INTERMEDIATE_EVENT, MESSAGE_EVENT)
            if WordNetWrapper.is_verb_of_type(action.f_name, SEND):
                message_event.sub_type = THROWING_EVENT
            return message_event

        return Event(INTERMEDIATE_EVENT)

    def get_event_text(self, action):
        pass

    def get_lane(self, actor):
        subject = actor.f_subjectRole

        if actor.f_needsResolve:
            if isinstance(actor.f_reference, Actor):
                actor = actor.f_reference
            else:
                return None

        if not actor.f_unreal and not actor.f_metaActor and subject:
            name = self.get_name(actor, False, 1, False)
            self.f_actor_name_map[actor] = name

            if not name in self.f_name_pool_map:
                lane = Lane(name, self.f_main_pool)
                self.f_main_pool.append(lane)
                self.f_model.f_nodes.append(lane)
                self.name_pool_map[name] = lane
                return lane
            else:
                return self.f_name_pool_map[name]

        return None

    def to_process_node(self, action):
        if action in self.f_action_flow_map:
            return self.f_action_flow_map[action]
        else:
            if isinstance(action, DummyAction):
                task = Task()
                task.text = DUMMY_NODE
                self.f_action_flow_map[action] = task
                self.f_flow_action_map[task] = action
                return task
            else:
                self.logger.error("FlowObject not found!")
                return None

    def create_gateway(self, flow):
        gateway = Gateway()
        if flow.f_type == CONCURRENCY:
            gateway.type = PARALLEL_GATEWAY
        elif flow.f_type == MULTIPLE_CHOICE:
            gateway.type = INCLUSIVE_GATEWAY
        else:
            # Default type
            gateway.f_type = EVENT_BASED_GATEWAY
            for action in flow.f_multiples:
                node = self.f_action_flow_map.get(action, None)
                if isinstance(node, Event) and node.class_type == INTERMEDIATE_EVENT and not node.class_sub_type:
                    continue
                else:
                    gateway.type = EXCLUSIVE_GATEWAY
                    break

        self.f_model.f_nodes.append(gateway)
        return gateway

    def add_to_prevalent_lane(self, flow, gateway):
        lane_count = {}
        actions = [flow.f_single]

        actions.extend(flow.f_multiples)

        for action in actions:
            if not isinstance(action, DummyAction):
                lane = self.get_lane_for_node(self.to_process_node(action))
                lane_count[lane] = lane_count.get(lane, 0) + 1

        if len(lane_count) > 0:
            lane = max(lane_count, key=dict.get)
            lane.process_nodes.append(gateway)

    def add_to_same_lane(self, source, node):
        lane = self.get_lane_for_node(source)
        if lane:
            lane.process_nodes.append(node)

    def get_lane_for_node(self, source):
        pass

    def remove_node(self, node):
        pred_edge = None
        succ_edge = None

        for edge in self.f_model.f_edges:
            if edge.target == node:
                pred_edge = edge
            if edge.source == node:
                succ_edge = edge

        # TODO: check if this is enough
        self.f_model.f_nodes.remove(node)

        if pred_edge and succ_edge:
            self.f_model.f_edges.remove(pred_edge)
            self.f_model.f_edges.remove(succ_edge)
            sequence_flow = SequenceFlow(pred_edge.source, succ_edge.target)
            self.f_model.f_flows.append(sequence_flow)
            return sequence_flow
        else:
            return None
