from core.Base import Base
from utils import Processing
from utils.Constants import *
from utils import Search
from data.BPMNElements import *
from data.SentenceElements import *
from data.TextElements import DummyAction


class ProcessModelBuilder(Base):

    def __init__(self, world_model):
        self.f_world = world_model
        self.f_model = ProcessModel()
        self.f_flow_action_map = {}
        self.f_action_flow_map = {}
        self.f_actor_name_map = {}
        self.f_name_pool_map = {}
        self.f_main_pool = None
        self.f_not_assigned = []
        self.f_last_pool = None
        self.node_element_map = {}

    def create_process_model(self):
        self.f_main_pool = Pool("Pool")
        self.f_model.nodes.append(self.f_main_pool)

        self.create_actions()
        self.build_sequence_flows()
        self.remove_dummies()
        self.finish_dangling_ends()
        self.process_meta_activities()

        if len(self.f_main_pool.process_nodes) == 0:
            self.f_model.remove_node(self.f_main_pool)

        # TODO: check if necessary
        # self.build_black_box_pools()
        # self.build_data_objects()

        return self.f_model

    def create_actions(self):
        for action in self.f_world.f_actions:
            if action.f_marker != IF and not action.f_markerFromPP:
                flow_object = self.create_task(action)
            else:
                flow_object = self.create_event_node(action)
                self.f_model.nodes.append(flow_object)
                self.node_element_map[flow_object] = action
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
                self.f_model.edges.append(sequence_flow)
                self.node_element_map[sequence_flow] = flow
            elif flow.f_type == EXCEPTION:
                exception_event = Event(INTERMEDIATE_EVENT, ERROR_EVENT)
                self.f_model.nodes.append(exception_event)
                self.node_element_map[exception_event] = flow
                task = self.to_process_node(flow.f_single)
                exception_event.parent_node = task
                self.add_to_same_lane(task, exception_event)

                sequence_flow = SequenceFlow(exception_event,
                                             self.to_process_node(flow.f_multiples[0]))
                self.f_model.edges.append(sequence_flow)
                self.node_element_map[sequence_flow] = flow
            elif flow.f_direction == SPLIT:
                gateway = self.create_gateway(flow)
                sequence_flow = SequenceFlow(self.to_process_node(flow.f_single), gateway)
                self.f_model.edges.append(sequence_flow)
                self.node_element_map[sequence_flow] = flow
                self.add_to_prevalent_lane(flow, gateway)
                for action in flow.f_multiples:
                    internal_flow = SequenceFlow(gateway, self.to_process_node(action))
                    self.f_model.edges.append(internal_flow)
                    self.node_element_map[internal_flow] = flow
            elif flow.f_direction == JOIN:
                gateway = self.create_gateway(flow)
                sequence_flow = SequenceFlow(gateway, self.to_process_node(flow.f_single))
                self.f_model.edges.append(sequence_flow)
                self.node_element_map[sequence_flow] = flow
                self.add_to_prevalent_lane(flow, gateway)
                for action in flow.f_multiples:
                    internal_flow = SequenceFlow(self.to_process_node(action), gateway)
                    self.f_model.edges.append(internal_flow)
                    self.node_element_map[internal_flow] = flow

    def remove_dummies(self):
        for action in self.f_world.f_actions:
            if isinstance(action, DummyAction) or action.f_transient or self.f_action_flow_map[action].text == DUMMY_NODE:
                self.remove_node(self.to_process_node(action))

    def finish_dangling_ends(self):
        source_map = {}
        target_map = {}

        # Calculating the occurrences of each node as a source and as a target
        for edge in self.f_model.edges:
            source_map[edge.source] = source_map.get(edge.source, 0) + 1
            target_map[edge.target] = target_map.get(edge.target, 0) + 1

        for node in self.f_model.nodes:
            if isinstance(node, Activity) or isinstance(node, Gateway) or (isinstance(node, Event) and node.class_type == INTERMEDIATE_EVENT):
                # If the node is not present, add it with 0 occurrences
                source_map.setdefault(node, 0)
                target_map.setdefault(node, 0)

                if source_map[node] == 0 or (isinstance(node, Gateway) and source_map[node] == 1 and target_map[node] == 1):
                    end_event = Event(END_EVENT)
                    self.f_model.nodes.append(end_event)
                    self.node_element_map[end_event] = self.node_element_map[node]
                    self.add_to_same_lane(node, end_event)
                    sequence_flow = SequenceFlow(node, end_event)
                    self.f_model.edges.append(sequence_flow)
                if target_map[node] == 0:
                    if isinstance(node, Event) and node.class_type == INTERMEDIATE_EVENT and node.parent_node:
                        continue
                    else:
                        start_event = Event(START_EVENT)
                        self.f_model.nodes.append(start_event)
                        self.node_element_map[start_event] = self.node_element_map[node]
                        self.add_to_same_lane(node, start_event)
                        sequence_flow = SequenceFlow(start_event, node)
                        self.f_model.edges.append(sequence_flow)

    def process_meta_activities(self):
        for action in self.f_world.f_actions:
            if action.f_actorFrom and action.f_actorFrom.f_metaActor:
                if WordNetWrapper.is_verb_of_type(action.f_name, END_VERB):
                    node = self.f_action_flow_map[action]
                    successors = self.f_model.get_successors(node)
                    self.remove_node(node)
                    if len(successors) == 1 and isinstance(successors[0], Event) and successors[0].class_type == END_EVENT:
                        if action.f_name == TERMINATE:
                            successors[0].class_sub_type = TERMINATE_EVENT
                elif WordNetWrapper.is_verb_of_type(action.f_name, START_VERB):
                    node = self.f_action_flow_map[action]
                    predecessors = self.f_model.get_predecessors(node)
                    if len(predecessors) == 1 and isinstance(predecessors[0], Event) and predecessors[0].class_type == START_EVENT:
                        self.remove_node(node)

    def create_task(self, action):
        task = Activity()
        name = self.create_task_text(action)
        task.text = name
        self.f_model.nodes.append(task)
        self.node_element_map[task] = action
        return task

    def create_task_text(self, action):
        text = ""
        if action.f_negated:
            if action.f_aux:
                text += action.f_aux + " "
            text += "not "

        if WordNetWrapper.is_weak_action(action) and self.can_be_transformed(action):
            if action.f_actorFrom and action.f_actorFrom.f_unreal and self.has_hidden_action(action.f_actorFrom):
                text += self.transform_to_action(action.f_actorFrom)
            elif action.f_object and (isinstance(action.f_object, Resource) or not action.f_object.f_unreal):
                text += self.transform_to_action(action.f_object)
        else:
            weak_verb = WordNetWrapper.is_weak_verb(action.f_name)
            if not weak_verb:
                text += WordNetWrapper.get_base_form(action.f_name) + " "
                if action.f_prt:
                    text += action.f_prt + " "
            # elif (not action.f_actorFrom or action.f_actorFrom.f_metaActor) and not action.f_xcomp:
            #     # TODO: if REMOVE_LOW_ENTROPY_NODES
            #     return DUMMY_NODE
            elif not action.f_xcomp:
                text += self.get_event_text(action)
                return " ".join(text.split())

            xcomp_added = False
            mod_added = False

            if action.f_object:
                if action.f_mod and action.f_modPos < action.f_object.f_word_index:
                    text += " " + action.f_mod + " "
                    mod_added = True
                if action.f_xcomp and action.f_xcomp.f_word_index < action.f_object.f_word_index:
                    text += " " + self.get_xcomp_text(action, not weak_verb) + " "
                    xcomp_added = True
                for spec in action.get_specifiers(IOBJ):
                    text += spec.f_name + " "
                text += self.get_name(action.f_object, True, 1, False)
                for spec in action.get_specifiers(DOBJ):
                    text += " " + spec.f_name

            if not mod_added and action.f_mod:
                text += " " + action.f_mod

            if not xcomp_added and action.f_xcomp:
                text += " " + self.get_specifiers_text(action, action.f_xcomp.f_word_index, True)
                text += " " + self.get_xcomp_text(action, not weak_verb or action.f_object is not None)

            xcomp_pos = action.f_xcomp.f_word_index if action.f_xcomp else -1
            text += " " + self.get_specifiers_text(action, xcomp_pos, False)

            if action.f_object:
                for spec in action.get_specifiers(PP):
                    if spec.f_name.startswith((TO, IN, ABOUT)) \
                            and not Search.starts_with(f_conditionIndicators, spec.f_name):
                        if spec.f_object:
                            text += " " + spec.f_headWord + " " + self.get_name(spec.f_object, True, 1, False)
                        else:
                            text += " " + spec.f_name
                            break

        return " ".join(text.split())

    @staticmethod
    def create_event_node(action):
        for spec in action.f_specifiers:
            for word in spec.f_name.split(" "):
                if WordNetWrapper.is_time_period(word):
                    timer_event = Event(INTERMEDIATE_EVENT, TIMER_EVENT)
                    timer_event.text = spec.f_name
                    return timer_event

        if WordNetWrapper.is_verb_of_type(action.f_name, SEND_VERB) or WordNetWrapper.is_verb_of_type(action.f_name, RECEIVE_VERB):
            message_event = Event(INTERMEDIATE_EVENT, MESSAGE_EVENT)
            if WordNetWrapper.is_verb_of_type(action.f_name, SEND_VERB):
                message_event.sub_type = THROWING_EVENT
            return message_event

        return Event(INTERMEDIATE_EVENT)

    def get_event_text(self, action):
        text = ""
        actor_plural = False

        if action.f_actorFrom:
            text += self.get_name(action.f_actorFrom, True, 1, False) + " "
            actor_plural = action.f_actorFrom.f_name.endswith("s")

        if WordNetWrapper.is_weak_verb(action.f_name) or action.f_cop or \
                action.f_object or len(action.f_specifiers) > 0 or action.f_negated:
            is_do = action.f_aux and WordNetWrapper.get_base_form(action.f_aux) == DO

            if action.f_negated and (not WordNetWrapper.is_weak_verb(action.f_name) or is_do):
                if action.f_aux and not WordNetWrapper.get_base_form(action.f_aux) == BE:
                    text += action.f_aux
                else:
                    text += DO if actor_plural else Processing.get_third_person(DO)

                text += " not " + WordNetWrapper.get_base_form(action.f_name) + " "
            else:
                if action.f_aux:
                    if action.f_actorFrom and not action.f_actorFrom.f_passive:
                        text += action.f_aux + " " + action.f_name
                    else:
                        text += Processing.get_third_person(action.f_name)
                else:
                    text += WordNetWrapper.get_base_form(action.f_name) if actor_plural else Processing.get_third_person(action.f_name)

                if action.f_negated:
                    text += " not "

            text += " "

        if action.f_cop:
            text += action.f_cop
        elif action.f_object:
            text += self.get_name(action.f_object, True, 1, False)
        elif len(action.f_specifiers) > 0:
            text += action.f_specifiers[0].f_name

        return text

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
                lane = Lane(name, self.f_main_pool)
                self.f_main_pool.process_nodes.append(lane)
                self.f_model.nodes.append(lane)
                self.node_element_map[lane] = actor
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
                task = Activity()
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
            gateway.type = EVENT_BASED_GATEWAY
            for action in flow.f_multiples:
                node = self.f_action_flow_map.get(action)
                if isinstance(node, Event) and node.class_type == INTERMEDIATE_EVENT and not node.class_sub_type:
                    continue
                else:
                    gateway.type = EXCLUSIVE_GATEWAY
                    break

        self.f_model.nodes.append(gateway)
        self.node_element_map[gateway] = flow
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
        if node in self.node_element_map:
            del(self.node_element_map[node])

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

    def can_be_transformed(self, action):
        if action.f_object and not Processing.is_unreal_actor(action.f_object) \
                and not action.f_object.f_needsResolve and self.has_hidden_action(action.f_object):
            return True

        return action.f_actorFrom and Processing.is_unreal_actor(action.f_actorFrom) and self.has_hidden_action(action.f_actorFrom)

    @staticmethod
    def has_hidden_action(obj):
        can_be_gerund = False
        for spec in obj.get_specifiers(PP):
            if spec.f_name.startswith(OF):
                can_be_gerund = True
                break

        if not can_be_gerund:
            return False

        for word in obj.f_name.split():
            if WordNetWrapper.derive_verb(word):
                return True

        return False

    def transform_to_action(self, obj):
        text = ""
        for word in obj.f_name.split():
            verb = WordNetWrapper.derive_verb(word)
            if verb:
                text += verb
                break
        for spec in obj.get_specifiers(PP):
            if spec.startswith(OF) and spec.f_object:
                text += " " + self.get_name(spec.f_object, True, 1, False)

        return text

    def get_xcomp_text(self, action, need_aux):
        text = ""
        if need_aux:
            if action.f_xcomp.f_aux:
                text += " " + action.f_xcomp.f_aux + " "
            else:
                text += " to "
        text += self.create_task_text(action.f_xcomp)
        return text

    def get_specifiers_text(self, action, limit, strict_before):
        text = ""
        if not action.f_object:
            specs = action.get_specifiers(PP)

            if not action.f_xcomp:
                specs.extend(action.get_specifiers(SBAR))

            specs = reversed(specs)
            found = False

            for spec in specs:
                if spec.f_type == SBAR and found:
                    break
                if spec.f_word_index > action.f_word_index:
                    before = spec.f_word_index < limit
                    if before == strict_before and self.consider_phrase(spec):
                        found = True
                        if spec.f_object:
                            text += " " + spec.f_headWord + " " + self.get_name(spec.f_object, True, 1, False)
                        else:
                            text += " " + spec.f_name

        return text

    @staticmethod
    def consider_phrase(spec):
        return spec.f_type not in (PERIPHERAL, EXTRA_THEMATIC)
