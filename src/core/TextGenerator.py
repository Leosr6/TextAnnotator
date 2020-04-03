from core.Base import Base
from data.BPMNElements import *
from data.SentenceElements import Element


class TextGenerator(Base):

    def __init__(self, text_analyzer, model_builder):
        self.text_analyzer = text_analyzer
        self.model_builder = model_builder

    def create_metadata(self):

        stanford_sentences = self.text_analyzer.f_raw_sentences
        element_flow_object_map = self.model_builder.element_flow_object_map

        metadata = {
            "processList": [],
            "text": self.create_text(stanford_sentences, element_flow_object_map)
        }

        return metadata

    def create_text(self, stanford_sentences, element_flow_object_map):

        text = {}

        for sentence in stanford_sentences:
            text[sentence] = {"value": str(sentence),
                              "snippetList": [],
                              "newSplitPath": False}

        for element, flow_object in element_flow_object_map.items():
            if isinstance(flow_object, FlowObject):
                sentence = text.get(element.f_sentence, None)
                if sentence:
                    if isinstance(flow_object, Gateway):
                        sentence["newSplitPath"] = True
                    # TODO: check if it's necessary to have a processId
                    snippet = {
                        "startIndex": self.get_element_start_index(element),
                        "endIndex": self.get_element_end_index(element),
                        "processElementId": id(flow_object),
                        "processElementType": self.get_element_type(flow_object),
                        "resourceId": self.get_resource_id(flow_object),
                        "processId": 0,
                        "level": self.get_object_level(flow_object)
                    }
                    sentence["snippetList"].append(snippet)

        return list(text.values())

    @staticmethod
    def get_element_type(flow_object):
        element_type = ""

        if isinstance(flow_object, Activity):
            element_type = "ACTIVITY"
        elif isinstance(flow_object, Event):
            # TODO: check event sub_type
            element_type = flow_object.class_sub_type + flow_object.class_type if flow_object.class_sub_type else flow_object.class_type
        elif isinstance(flow_object, Gateway):
            element_type = flow_object.type

        return element_type

    def get_resource_id(self, flow_object):
        for node in self.model_builder.f_model.nodes:
            if isinstance(node, Lane) and flow_object in node.process_nodes:
                return id(node)

        return -1

    def get_object_level(self, flow_object):

        pool = flow_object
        level = -1
        keep_searching = True

        while keep_searching:
            keep_searching = False
            for node in self.model_builder.f_model.nodes:
                if isinstance(node, Cluster) and pool in node.process_nodes:
                    level += 1
                    pool = node
                    keep_searching = True
                    break

        return level

    def get_element_start_index(self, element):
        index = -1

        if isinstance(element, Element):
            index = element.f_word_index
        elif element.f_single:
            index = element.f_single.f_word_index

        return index

    def get_element_end_index(self, element):
        index = -1

        if isinstance(element, Element):
            index = element.f_word_index + len(element.f_name)
        elif element.f_multiples:
            index = max(map(lambda action: action.f_word_index, element.f_multiples))
        elif element.f_single:
            index = element.f_single.f_word_index

        return index
