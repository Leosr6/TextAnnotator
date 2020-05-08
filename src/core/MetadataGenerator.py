from core.Base import Base
from data.BPMNElements import *
from data.TextElements import *
from data.SentenceElements import *
from utils import Search
from utils.Constants import *
from copy import copy


class MetadataGenerator(Base):

    def __init__(self, text_analyzer, model_builder):
        self.text_analyzer = text_analyzer
        self.model_builder = model_builder
        self.element_id_map = {}
        self.process_nodes = {}
        self.process_gateways = {}
        self.branch_actions = {}
        self.retricted_actions = {}

    def create_metadata(self):

        stanford_sentences = self.text_analyzer.f_raw_sentences

        self.create_ids()
        self.extract_process_elements()

        metadata = {
            "resourceList": self.create_resource_list(),
            "text": self.create_text(stanford_sentences),
            "gateways": self.create_gateways()
        }

        return metadata

    def create_ids(self):
        element_id = 0

        for node in self.model_builder.f_model.nodes:
            if isinstance(node, FlowObject) or isinstance(node, Lane):
                self.element_id_map[node] = "id-{}".format(element_id)
                element_id += 1

    def extract_process_elements(self):

        nodes = set()
        gateways = set()
        ignored_actions = set()
        restricted_actions = set()
        branch_actions = set()

        action_branch_map = {}
        for node in self.model_builder.f_model.nodes:
            if isinstance(node, Lane):
                nodes.add(node)
            elif isinstance(node, Gateway):
                flow = node.element
                if flow.f_direction == SPLIT:
                    for branch in flow.f_multiples:
                        action_branch_map.setdefault((branch.f_sentence.f_id, branch.f_word_index), []).append(branch)
                        if flow.f_type == CHOICE:
                            branch_actions.add(branch)
                else:
                    if flow.f_type == CHOICE:
                        for branch in flow.f_multiples:
                            if branch in branch_actions:
                                branch_actions.remove(branch)

        for branch_list in action_branch_map.values():
            if len(branch_list) > 1:
                restricted_actions.add(branch_list[0])
                ignored_actions.update(branch_list[1:])

        self.retricted_actions = restricted_actions
        self.branch_actions = branch_actions
        ignored_actions.update(branch_actions)

        for edge in self.model_builder.f_model.edges:
            if isinstance(edge.source, Gateway):
                gateways.add(edge.source)
            elif edge.source.element not in ignored_actions:
                nodes.add(edge.source)
            if isinstance(edge.target, Gateway):
                gateways.add(edge.target)
            elif edge.target.element not in ignored_actions:
                nodes.add(edge.target)

        self.process_nodes = nodes
        self.process_gateways = gateways

    def create_resource_list(self):

        resource_list = []
        for node in self.model_builder.f_model.nodes:
            if isinstance(node, Lane):
                resource_list.append({"id": self.element_id_map[node], "name": node.name})

        return resource_list

    def create_text(self, stanford_sentences):

        text = {}
        stanford_sentences.sort(key=lambda s: s.f_id)

        for sentence in stanford_sentences:
            text[sentence] = {
                "sentenceId": sentence.f_id,
                "value": str(sentence),
                "snippetList": []
            }

        for node in self.process_nodes:
            element = node.element
            sentence = text.get(element.f_sentence)
            if sentence:
                snippet = {
                    "startIndex": self.get_element_start_index(element),
                    "endIndex": self.get_element_end_index(element),
                    "processElementId": self.element_id_map[node],
                    "processElementType": self.get_node_type(node),
                    "resourceId": self.get_resource_id(node),
                    "level": self.get_object_level(node)
                }
                sentence["snippetList"].append(snippet)

        for sentence in text.values():
            sentence["snippetList"].sort(key=lambda snpt: snpt["startIndex"])

        return [text[sentence] for sentence in stanford_sentences]

    def create_gateways(self):

        gateway_list = []

        for gateway in self.process_gateways:

            gateway_data = {
                "processElementId": self.element_id_map[gateway],
                "processElementType": self.get_node_type(gateway),
                "resourceId": self.get_resource_id(gateway),
                "level": self.get_object_level(gateway),
                "branches": []
            }

            # Order gateway branches by sentence id
            gateway.element.f_multiples.sort(key=lambda action: action.f_sentence.f_id)

            # In a split, all branches are added
            if gateway.element.f_direction == SPLIT:
                for element in gateway.element.f_multiples:
                    start_index, end_index, is_explicit = self.get_split_index(gateway, element)
                    gateway_data["branches"].append({
                        "startIndex": start_index,
                        "endIndex": end_index,
                        "sentenceId": element.f_sentence.f_id,
                        "isExplicit": is_explicit
                    })
            else:
                element, start_index, end_index, is_explicit = self.get_join_index(gateway)
                gateway_data["branches"].append({
                    "startIndex": start_index,
                    "endIndex": end_index,
                    "sentenceId": element.f_sentence.f_id,
                    "isExplicit": is_explicit
                })

            gateway_data["branches"].sort(key=lambda snpt: (snpt["sentenceId"], snpt["startIndex"]))
            gateway_list.append(gateway_data)

        gateway_list.sort(key=lambda gtw: (gtw["branches"][0]["sentenceId"], gtw["branches"][0]["startIndex"]))

        return gateway_list

    def get_join_index(self, gateway):
        explicit = False
        start_index = None
        end_index = None
        element = self.get_next_element(gateway)

        branches = gateway.element.f_multiples
        branches.sort(key=lambda action: (action.f_sentence.f_id, action.f_word_index))

        if element:
            sentence = element.f_sentence.f_tree.leaves()
            last_branch = branches[-1]
            for indicator in WordNetWrapper.accepted_forward_links:
                part = indicator.split()
                indicator_index = Search.find_array_part(sentence, part)
                if indicator_index != -1:
                    if element.f_word_index > indicator_index:
                        if (element.f_sentence.f_id, indicator_index) > (last_branch.f_sentence.f_id, self.get_element_end_index(last_branch)):
                            start_index = indicator_index
                            end_index = indicator_index + len(part) - 1
                            explicit = True

        if not explicit:
            element = branches[-1]
            start_index = self.get_element_end_index(element) + 1
            end_index = start_index

        return element, start_index, end_index, explicit

    def get_next_element(self, source):
        for edge in self.model_builder.f_model.edges:
            if edge.source == source:
                node = edge.target
                if isinstance(node, Gateway):
                    return node.element.f_multiples[0]
                else:
                    return node.element

        return None

    @staticmethod
    def get_node_type(node):
        node_type = ""
        element = node.element

        if isinstance(node, Task):
            node_type = "TASK"
        elif isinstance(node, Lane):
            node_type = "LANE"
        elif isinstance(node, Gateway):
            if node.type == EXCLUSIVE_GATEWAY:
                node_type = "XORSPLIT" if element.f_direction == SPLIT else "XORJOIN"
            elif node.type == PARALLEL_GATEWAY:
                node_type = "ANDSPLIT" if element.f_direction == SPLIT else "ANDJOIN"
            elif node.type == INCLUSIVE_GATEWAY:
                node_type = "ORSPLIT" if element.f_direction == SPLIT else "ORJOIN"
            elif node.type == EVENT_BASED_GATEWAY:
                node_type = EVENT_BASED_GATEWAY
            else:
                node_type = node.type
        elif isinstance(node, Event):
            # TODO: check event sub_type
            node_type = node.class_sub_type + node.class_type if node.class_sub_type else node.class_type
            # node_type = node.class_type

        return node_type.upper()

    def get_resource_id(self, node):
        for resource in self.model_builder.f_model.nodes:
            if isinstance(resource, Lane) and node in resource.process_nodes:
                return self.element_id_map[resource]

        if isinstance(node, Lane):
            return self.element_id_map[node]

        return -1

    def get_object_level(self, flow_object):

        source = flow_object
        level = 0
        keep_searching = True

        # Corner case when the flow_object is a Split Gateway
        if isinstance(source, Gateway) and source.element.f_direction == SPLIT:
            level = -1

        while keep_searching:
            if isinstance(source, Gateway):
                if source.element.f_direction == SPLIT:
                    level += 1
                else:
                    level -= 1

            keep_searching = False
            for sequence_flow in self.model_builder.f_model.edges:
                if sequence_flow.target == source:
                    source = sequence_flow.source
                    keep_searching = True
                    break

        return level

    def get_split_index(self, node, element):
        start_index = None
        end_index = None
        explicit = True

        if node.type == EXCLUSIVE_GATEWAY:
            if element.f_marker in f_conditionIndicators:
                start_index = element.f_markerPos
                end_index = self.get_element_end_index(element) if element in self.branch_actions else start_index
            elif element.f_preAdvMod in f_conditionIndicators:
                start_index = element.f_preAdvModPos
                end_index = self.get_element_end_index(element) if element in self.branch_actions else start_index
        elif node.type == PARALLEL_GATEWAY:
            if element.f_marker in f_parallelIndicators:
                start_index = element.f_markerPos
                end_index = start_index

        if not start_index or not end_index:
            element_to_mark = self.find_branch_element(node, element)
            start_index = self.get_element_start_index(element_to_mark)
            end_index = self.get_element_end_index(element_to_mark)
            explicit = False

        return start_index, end_index, explicit

    def find_branch_element(self, gateway, action):
        action_list = copy(gateway.element.f_multiples)
        action_list.remove(action)

        if action.f_actorFrom and len([x for x in action_list if x.f_actorFrom == action.f_actorFrom]) == 0:
            return action.f_actorFrom

        if len([x for x in action_list if x.f_word_index == action.f_word_index]) == 0:
            return action

        if action.f_object and len([x for x in action_list if x.f_object == action.f_object]) == 0:
            return action.f_object

        return action

    def get_element_start_index(self, element):
        candidates = []

        if isinstance(element, Actor) or isinstance(element, Resource):
            det = 1 if element.f_determiner else 0
            candidates.append(element.f_word_index - det)
            for spec in element.f_specifiers:
                candidates.append(spec.f_word_index - det)
        elif isinstance(element, DummyAction):
            candidates.append(element.f_word_index)
        elif isinstance(element, Action):
            candidates.append(element.f_word_index)

            if element.f_aux:
                candidates[0] -= 1

            if element.f_object:
                det = 1 if element.f_object.f_determiner else 0
                candidates.append(element.f_object.f_word_index - det)
                for spec in element.f_object.f_specifiers:
                    candidates.append(spec.f_word_index - det)

        return min([candidate for candidate in candidates if candidate > 0], default=1)

    def get_element_end_index(self, element, xcomp=False):
        candidates = []

        if isinstance(element, Actor) or isinstance(element, Resource):
            candidates.append(element.f_word_index)
            for spec in element.f_specifiers:
                candidates.append(spec.f_word_index)
        elif isinstance(element, DummyAction):
            candidates.append(element.f_word_index)
        elif isinstance(element, Action):
            candidates.append(element.f_word_index)

            if element.f_cop:
                candidates.append(element.f_copIndex)

            if element not in self.retricted_actions:
                if not xcomp:
                    for spec in element.f_specifiers:
                        if spec.f_word_index > element.f_word_index:
                            candidates.append(spec.f_word_index + spec.f_name.count(" "))

                if element.f_object:
                    if element.f_object.f_word_index > element.f_word_index:
                        candidates.append(element.f_object.f_word_index + element.f_object.f_name.count(" "))
                        for spec in element.f_object.f_specifiers:
                            if spec.f_word_index > element.f_word_index:
                                candidates.append(spec.f_word_index + spec.f_name.count(" "))

                if element.f_xcomp:
                    candidates.append(self.get_element_end_index(element.f_xcomp, xcomp=True))

        return max(candidates, default=1)
