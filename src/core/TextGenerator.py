from core.Base import Base
from data.BPMNElements import *
from data.TextElements import *
from utils.Constants import *


class TextGenerator(Base):

    def __init__(self, text_analyzer, model_builder):
        self.text_analyzer = text_analyzer
        self.model_builder = model_builder
        self.element_id_map = {}
        self.process_id_map = {}

    def create_metadata(self):

        stanford_sentences = self.text_analyzer.f_raw_sentences

        self.create_ids()

        metadata = {
            "processList": self.create_process_list(),
            "text": self.create_text(stanford_sentences)
        }

        return metadata

    def create_ids(self):
        element_id = 0
        process_id = 0

        for node in self.model_builder.f_model.nodes:
            if isinstance(node, Pool):
                self.process_id_map[node] = "id-{}".format(process_id)
                process_id += 1

        for node in self.model_builder.node_element_map.keys():
            if not isinstance(node, SequenceFlow):
                self.element_id_map[node] = "id-{}".format(element_id)
                element_id += 1

    def create_process_list(self):
        process_list = []

        for pool, process_id in self.process_id_map.items():
            resource_list = []
            for node in pool.process_nodes:
                if isinstance(node, Lane):
                    resource_list.append({"id": self.element_id_map[node], "name": node.name})
            process_list.append({
                "resourceList": resource_list,
                "id": process_id,
                "name": pool.name
            })

        return process_list

    def create_text(self, stanford_sentences):

        text = {}
        stanford_sentences.sort(key=lambda s: s.f_id)

        for sentence in stanford_sentences:
            text[sentence] = {
                "value": str(sentence),
                "snippetList": [],
                "newSplitPath": False
            }

        for node, element in self.model_builder.node_element_map.items():
            if isinstance(node, FlowObject):
                sentence = text.get(element.f_single.f_sentence) if isinstance(node, Gateway) else text.get(element.f_sentence)
                if sentence:
                    snippet = {
                        "startIndex": self.get_element_start_index(element),
                        "endIndex": self.get_element_end_index(element),
                        "processElementId": self.element_id_map[node],
                        "processElementType": self.get_element_type(element, node),
                        "resourceId": self.get_resource_id(node),
                        "processId": self.get_process_id(node),
                        "level": self.get_object_level(node)
                    }
                    sentence["snippetList"].append(snippet)
            if isinstance(node, Gateway) and element.f_direction == SPLIT:
                for multiples in element.f_multiples:
                    split_sentence = text.get(multiples.f_sentence)
                    if split_sentence:
                        split_sentence["newSplitPath"] = True

        return [text[sentence] for sentence in stanford_sentences]

    def get_process_id(self, flow_object):
        for pool, process_id in self.process_id_map.items():
            for lane in pool.process_nodes:
                if flow_object in lane.process_nodes:
                    return process_id

        return 0

    @staticmethod
    def get_element_type(element, flow_object):
        element_type = ""

        if isinstance(flow_object, Activity):
            element_type = "ACTIVITY"
        elif isinstance(flow_object, Gateway):
            if flow_object.type in (EXCLUSIVE_GATEWAY, EVENT_BASED_GATEWAY):
                element_type = "XORSPLIT" if element.f_direction == SPLIT else "XORJOIN"
            elif flow_object.type == PARALLEL_GATEWAY:
                element_type = "ANDSPLIT" if element.f_direction == SPLIT else "ANDJOIN"
            elif flow_object.type == INCLUSIVE_GATEWAY:
                element_type = "ORSPLIT" if element.f_direction == SPLIT else "ORJOIN"
            else:
                element_type = flow_object.type
        elif isinstance(flow_object, Event):
            # TODO: check event sub_type
            element_type = flow_object.class_sub_type + flow_object.class_type if flow_object.class_sub_type else flow_object.class_type

        return element_type.upper()

    def get_resource_id(self, flow_object):
        for node in self.model_builder.f_model.nodes:
            if isinstance(node, Lane) and flow_object in node.process_nodes:
                return self.element_id_map[node]

        return -1

    def get_object_level(self, flow_object):

        source = flow_object
        level = 0
        keep_searching = True

        # Corner case when the flow_object is a Split Gateway
        if isinstance(source, Gateway) and self.model_builder.node_element_map[source].f_direction == SPLIT:
            level = -1

        while keep_searching:
            if isinstance(source, Gateway):
                if self.model_builder.node_element_map[source].f_direction == SPLIT:
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

    def get_element_start_index(self, element):
        candidates = []

        if isinstance(element, Flow):
            candidates.append(self.get_element_start_index(element.f_single))
            for multiple in element.f_multiples:
                candidates.append(self.get_element_start_index(multiple))
        elif isinstance(element, DummyAction):
            return 1
        elif isinstance(element, Action):
            candidates.append(element.f_word_index)

            for spec in element.f_specifiers:
                candidates.append(spec.f_word_index)

            if isinstance(element, Action):
                if element.f_aux:
                    candidates[0] -= 1

                if element.f_preAdvMod:
                    candidates.append(element.f_preAdvModPos)

                if element.f_object:
                    candidates.append(element.f_object.f_word_index)
                    if element.f_object.f_determiner:
                        candidates[-1] -= 1
                    for spec in element.f_object.f_specifiers:
                        candidates.append(spec.f_word_index)

                if element.f_actorFrom:
                    candidates.append(element.f_actorFrom.f_word_index)
                    if element.f_actorFrom.f_determiner:
                        candidates[-1] -= 1
                    for spec in element.f_actorFrom.f_specifiers:
                        candidates.append(spec.f_word_index)

        return min([candidate for candidate in candidates if candidate > 0])

    def get_element_end_index(self, element):
        candidates = []

        if isinstance(element, Flow):
            candidates.append(self.get_element_end_index(element.f_single))
            for multiple in element.f_multiples:
                candidates.append(self.get_element_end_index(multiple))
        elif isinstance(element, DummyAction):
            return 1
        elif isinstance(element, Action):
            candidates.append(element.f_word_index)

            for spec in element.f_specifiers:
                candidates.append(spec.f_word_index + spec.f_name.count(" "))

            if isinstance(element, Action):
                if element.f_object:
                    candidates.append(element.f_object.f_word_index + element.f_object.f_name.count(" "))
                    for spec in element.f_object.f_specifiers:
                        candidates.append(spec.f_word_index + spec.f_name.count(" "))

                if element.f_actorFrom:
                    candidates.append(element.f_actorFrom.f_word_index + element.f_actorFrom.f_name.count(" "))
                    for spec in element.f_actorFrom.f_specifiers:
                        candidates.append(spec.f_word_index + spec.f_name.count(" "))

        return max(candidates)
