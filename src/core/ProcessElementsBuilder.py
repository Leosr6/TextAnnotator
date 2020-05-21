from copy import copy
from core.Base import Base
from utils.Constants import *
from data.BPMNElements import *
from data.SentenceElements import *
from data.TextElements import DummyAction


class ProcessElementsBuilder(Base):

    def __init__(self, world_model):
        self.f_world = world_model
        self.f_model = ProcessModel()
        self.f_action_flow_map = {}
        self.f_actor_name_map = {}
        self.f_name_pool_map = {}
        self.f_main_pool = None
        self.f_not_assigned = []
        self.f_last_pool = None

    def create_process_model(self):
        self.f_main_pool = Pool()
        self.f_model.nodes.append(self.f_main_pool)

        self.create_actions()
        self.build_sequence_flows()
        self.remove_dummies()
        self.finish_dangling_ends()
        self.process_meta_activities()

        if len(self.f_main_pool.process_nodes) == 0:
            self.f_model.remove_node(self.f_main_pool)

        return self.f_model

    def create_actions(self):
        for action in self.f_world.f_actions:
            if self.is_event_action(action) or action.f_marker == IF or action.f_markerFromPP:
                flow_object = self.create_event_node(action)
            else:
                flow_object = Task(action)

            self.f_model.nodes.append(flow_object)
            self.f_action_flow_map[action] = flow_object

            if action.f_xcomp:
                self.f_action_flow_map[action.f_xcomp] = flow_object

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
                node = self.to_process_node(flow.f_single)
                timer_event = self.check_timer_event(flow.f_multiples[0])
                if timer_event:
                    self.f_model.nodes.append(timer_event)
                    self.add_to_same_lane(node, timer_event)
                    sequence_flow = SequenceFlow(timer_event, node)
                    self.f_model.edges.append(sequence_flow)
                sequence_flow = SequenceFlow(node, self.to_process_node(flow.f_multiples[0]))
                self.f_model.edges.append(sequence_flow)
            elif flow.f_direction == SPLIT:
                if len(flow.f_multiples) == 1:
                    event = self.to_process_node(flow.f_multiples[0])
                    event.class_sub_type = CONDITIONAL_EVENT
                    self.add_to_prevalent_lane(flow, event)
                    sequence_flow = SequenceFlow(self.to_process_node(flow.f_single), event)
                else:
                    gateway = self.create_gateway(flow)
                    self.add_to_prevalent_lane(flow, gateway)
                    sequence_flow = SequenceFlow(self.to_process_node(flow.f_single), gateway)
                    for action in flow.f_multiples:
                        internal_flow = SequenceFlow(gateway, self.to_process_node(action))
                        self.f_model.edges.append(internal_flow)
                self.f_model.edges.append(sequence_flow)
            elif flow.f_direction == JOIN:
                if len(flow.f_multiples) > 1:
                    gateway = self.create_gateway(flow)
                    sequence_flow = SequenceFlow(gateway, self.to_process_node(flow.f_single))
                    self.f_model.edges.append(sequence_flow)
                    self.add_to_prevalent_lane(flow, gateway)
                    for action in flow.f_multiples:
                        internal_flow = SequenceFlow(self.to_process_node(action), gateway)
                        self.f_model.edges.append(internal_flow)

    def remove_dummies(self):
        for action in self.f_world.f_actions:
            if isinstance(action, DummyAction) or action.f_transient:
                self.remove_node(self.to_process_node(action))

    def finish_dangling_ends(self):
        source_map = {}
        target_map = {}

        # Calculating the occurrences of each node as a source and as a target
        for edge in self.f_model.edges:
            source_map[edge.source] = source_map.get(edge.source, 0) + 1
            target_map[edge.target] = target_map.get(edge.target, 0) + 1

        current_nodes = copy(self.f_model.nodes)

        for node in current_nodes:
            if isinstance(node, Task) or isinstance(node, Gateway) or (isinstance(node, Event) and node.class_type == INTERMEDIATE_EVENT):
                # If the node is not present, add it with 0 occurrences
                source_map.setdefault(node, 0)
                target_map.setdefault(node, 0)

                if source_map[node] == 0:
                    if isinstance(node, Gateway) and node.element.f_direction == JOIN:
                        transformed_elements = 0
                        branches = node.element.f_multiples
                        for element in branches:
                            branch = self.to_process_node(element)
                            if branch and self.check_end_event(branch):
                                transformed_elements += 1
                        # Only keep joins with more than 1 active branches
                        if len(branches) - transformed_elements <= 1:
                            self.remove_node(node)
                    else:
                        self.check_end_event(node)
                if target_map[node] == 0:
                    self.check_start_event(node)

    def process_meta_activities(self):
        for node in self.f_model.nodes:
            if isinstance(node, Task):
                element = node.element
                if element.f_actorFrom and element.f_actorFrom.f_metaActor:
                    self.check_end_event(node)
                    self.check_duplicated_start(node)

    def check_start_event(self, node):
        # A process model can start with a Message event
        if isinstance(node, Event) and node.class_sub_type not in (MESSAGE_EVENT, TIMER_EVENT):
            node.class_type = START_EVENT
            node.class_sub_type = ""
            node.class_spec = None

        return False

    def check_end_event(self, node):
        element = node.element

        if WordNetWrapper.is_verb_of_type(element.f_name, END_VERB):
            # A process model can end with a Message event
            if isinstance(node, Event):
                if node.class_type == END_EVENT or (node.class_sub_type == MESSAGE_EVENT and node.class_spec == THROWING_EVENT):
                    return False
            self.transform_end_event(node)
            return True

        return False

    def check_duplicated_start(self, node):
        element = node.element

        if WordNetWrapper.is_verb_of_type(element.f_name, START_VERB):
            predecessors = self.f_model.get_predecessors(node)
            if len(predecessors) == 1 and isinstance(predecessors[0], Event) and predecessors[0].class_type == START_EVENT:
                self.remove_node(node)

    def create_event_node(self, action):
        if WordNetWrapper.is_verb_of_type(action.f_name, SEND_VERB) or WordNetWrapper.is_verb_of_type(action.f_name, RECEIVE_VERB):
            if not action.f_actorFrom:
                message_event = Event(action, INTERMEDIATE_EVENT, MESSAGE_EVENT)
                if WordNetWrapper.is_verb_of_type(action.f_name, SEND_VERB):
                    message_event.class_spec = THROWING_EVENT
                else:
                    message_event.class_spec = CATCHING_EVENT
                return message_event

        if action.f_marker in f_conditionIndicators:
            return Event(action, INTERMEDIATE_EVENT, CONDITIONAL_EVENT)

        return Event(action, INTERMEDIATE_EVENT)

    def check_timer_event(self, action):
        for spec in action.f_specifiers:
            for word in spec.f_name.split():
                if word not in falseTimePeriod and WordNetWrapper.is_time_period(word):
                    return Event(spec, INTERMEDIATE_EVENT, TIMER_EVENT)

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

            if name not in self.f_name_pool_map:
                lane = Lane(actor, name, self.f_main_pool)
                self.f_main_pool.process_nodes.append(lane)
                self.f_model.nodes.append(lane)
                self.f_name_pool_map[name] = lane
                return lane
            else:
                return self.f_name_pool_map[name]

        return None

    def to_process_node(self, action):
        if action in self.f_action_flow_map:
            return self.f_action_flow_map[action]
        else:
            if isinstance(action, DummyAction):
                task = Task(action)
                self.f_action_flow_map[action] = task
                return task
            else:
                self.logger.error("FlowObject not found!")
                return None

    def create_gateway(self, flow):
        gateway = Gateway(flow)

        if flow.f_type == CONCURRENCY:
            gateway.type = PARALLEL_GATEWAY
        elif flow.f_type == MULTIPLE_CHOICE:
            gateway.type = INCLUSIVE_GATEWAY
        else:
            gateway.type = EXCLUSIVE_GATEWAY

        self.f_model.nodes.append(gateway)
        return gateway

    def add_to_prevalent_lane(self, flow, gateway):
        lane_count = {}
        actions = [flow.f_single]

        actions.extend(flow.f_multiples)

        for action in actions:
            if not isinstance(action, DummyAction):
                lane = self.get_lane_for_node(self.to_process_node(action))
                if lane:
                    lane_count[lane] = lane_count.get(lane, 0) + 1

        if len(lane_count) > 0:
            lane = max(lane_count, key=lane_count.get)
            lane.process_nodes.append(gateway)

    def add_to_same_lane(self, source, node):
        lane = self.get_lane_for_node(source)
        if lane:
            lane.process_nodes.append(node)

    def get_lane_for_node(self, source):
        for node in self.f_model.nodes:
            if isinstance(node, Lane):
                if source in node.process_nodes:
                    return node

        return None

    def remove_node(self, node):
        pred_edge = None
        succ_edge = None

        for edge in self.f_model.edges:
            if edge.target == node:
                pred_edge = edge
            if edge.source == node:
                succ_edge = edge

        self.f_model.remove_node(node)

        if pred_edge and succ_edge:
            sequence_flow = SequenceFlow(pred_edge.source, succ_edge.target)
            self.f_model.edges.append(sequence_flow)
            return sequence_flow
        else:
            return None

    def get_name(self, obj, add_det, level, compact):
        if not obj:
            return None
        if obj.f_needsResolve and isinstance(obj.f_reference, ExtractedObject):
            return self.get_name(obj.f_reference, add_det, 1, False)

        text = ""

        if add_det and obj.f_determiner in f_wantedDeterminers:
            text += obj.f_determiner + " "

        for spec in obj.get_specifiers(AMOD):
            text += spec.f_name + " "
        for spec in obj.get_specifiers(NUM):
            text += spec.f_name + " "
        for spec in obj.get_specifiers(NN):
            text += spec.f_name + " "

        text += obj.f_name

        for spec in obj.get_specifiers(NNAFTER):
            text += " " + spec.f_name

        if level <= MAX_NAME_DEPTH:
            for spec in obj.get_specifiers(PP):
                if spec.f_type == UNKNOWN and ADD_UNKNOWN_PHRASETYPES:
                    if spec.f_name.startswith(OF) or \
                            (not compact and spec.f_name.startswith((INTO, UNDER, ABOUT))):
                        text += " " + self.add_specifier(spec, level, compact)
                    elif self.consider_phrase(spec):
                        text += " " + self.add_specifier(spec, level, compact)

        if not compact:
            for spec in obj.get_specifiers(INFMOD):
                text += " " + spec.f_name
            for spec in obj.get_specifiers(PARTMOD):
                text += " " + spec.f_name

        return text

    def add_specifier(self, spec, level, compact):
        text = ""
        if spec.f_object:
            text += spec.f_headWord + " " + self.get_name(spec.f_object, True, level + 1, compact)
        else:
            text += spec.f_name
        return text

    @staticmethod
    def is_event_action(action):
        if (action.f_preAdvMod and not action.preAdvModFromSpec and action.f_preAdvMod != SOON) or action.f_marker:
            sentence = str(action.f_sentence).lower()
            s_id = action.f_sentence.f_id
            min_index = max((s_id, action.f_preAdvModPos), (s_id, action.f_markerPos))
            # Checking if the sentence contains any indicators that the activity has finished
            for indicator in finishedIndicators:
                indicator_index = sentence.find(indicator)
                if indicator_index != -1:
                    indicator_index += len(indicator.split())
                    if min_index <= (s_id, indicator_index) <= action.get_index():
                        return True

        return False

    def transform_end_event(self, node):

        end_event = Event(node.element, END_EVENT)
        self.f_model.nodes.append(end_event)
        self.add_to_same_lane(node, end_event)

        for edge in self.f_model.edges:
            if edge.target == node:
                edge.target = end_event

        self.remove_node(node)

    @staticmethod
    def consider_phrase(spec):
        return spec.f_type not in (PERIPHERAL, EXTRA_THEMATIC)
