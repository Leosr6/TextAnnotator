from copy import deepcopy
from core.CoreNLPWrapper import CoreNLPWrapper
from core.Base import Base
from data.WorldModel import WorldModel
from core.SentenceAnalyzer import SentenceAnalyzer
from core.WordNetWrapper import WordNetWrapper
from data.StanfordSentence import StanfordSentence
from data.SentenceElements import *
from data.TextElements import *
from utils import Search, Processing
from utils.Constants import *


class TextAnalyzer(Base):
    f_world = None
    f_text = ""
    f_parser = None
    f_analyzed_sentences = []
    f_raw_sentences = []
    f_reference_map = {}
    f_last_split = None

    def __init__(self):
        self.f_parser = CoreNLPWrapper()

    def analyze_text(self, text):

        self.f_text = text
        self.f_world = WorldModel()
        self.f_analyzed_sentences = []

        sentence_analyzer = SentenceAnalyzer(self.f_world)
        self.f_raw_sentences = self.create_stanford_sentences(text)

        for stanford_sentence in self.f_raw_sentences:
            self.f_analyzed_sentences.append(sentence_analyzer.analyze_sentence(stanford_sentence))

        self.reference_resolution()
        self.marker_detection()
        self.combine_actions()
        self.determine_links()
        self.build_flows()

    def create_stanford_sentences(self, text):

        # List of standford_sentences
        stanford_sentences = []

        sentences = self.f_parser.parse_text(text)

        for index, sentence in enumerate(sentences):
            tree, deps, tokens = sentence
            s_sentence = StanfordSentence(tree, deps, tokens, index)
            stanford_sentences.append(s_sentence)

        return stanford_sentences

    def reference_resolution(self):
        to_check = []
        to_check.extend(self.f_world.f_actors)
        to_check.extend(self.f_world.f_resources)

        for obj in to_check:
            if obj.f_needsResolve:
                self.logger.debug("Resolving {}".format(obj))
                sentence_word_id = (obj.f_sentence.f_id, obj.f_word_index)
                if sentence_word_id in self.f_reference_map:
                    target = self.f_reference_map[sentence_word_id]
                    element = self.to_element(target)
                    obj.f_reference = element
                    self.logger.debug("Manual resolution of {}".format(element))
                else:
                    sentence_id = obj.f_sentence.f_id
                    if Processing.is_action_resolution_determiner(obj.f_name):
                        action = self.find_action(sentence_id, obj)
                        obj.f_reference = action
                        self.logger.debug("Resolution result: {}".format(action))
                    else:
                        animate = self.determine_animate_type(obj)
                        containing_action = Search.get_action(self.f_world.get_actions_of_sentence(obj.f_sentence), obj)
                        invert_role_match = containing_action.f_cop or Processing.is_RC_pronoun(obj.f_name)
                        reference = self.find_reference(sentence_id, obj, animate, invert_role_match)
                        obj.f_reference = reference
                        self.logger.debug("Resolution result: {}".format(reference))

    def marker_detection(self):
        pass

    def combine_actions(self):
        for action in self.f_world.f_actions:
            reference_action = None
            if action.f_actorFrom and isinstance(action.f_actorFrom.f_reference, Action):
                reference_action = action.f_actorFrom.f_reference
            elif action.f_object and action.f_object.f_reference:
                if isinstance(action.f_object.f_reference, Action):
                    reference_action = action.f_object.f_reference
                else:
                    reference_action = Search.get_action(self.f_world.f_actions, action.f_object.f_reference)

            if reference_action:
                if self.can_be_merged(reference_action, action, False):
                    self.logger.debug("Merging {} and {}".format(reference_action, action))
                    self.merge(reference_action, action, False)
                elif self.can_be_merged(reference_action, action, True):
                    self.logger.debug("Copying attributes from {} to {}".format(reference_action, action))
                    action.f_actorFrom = reference_action.f_actorFrom
                    action.f_object = reference_action.f_object
                    action.f_cop = reference_action.f_cop
                    action.f_copIndex = reference_action.f_copIndex

    def determine_links(self):
        for first_action in self.f_world.f_actions:
            for second_action in self.f_world.f_actions:
                if first_action != second_action and self.is_linkable(first_action, second_action):
                    first_action.f_link = second_action
                    first_action.f_linkType = self.determine_link_type(first_action, second_action)
                    self.logger.debug("Linked actions {} and {}".format(first_action, second_action))

    def build_flows(self):
        self.f_last_split = None
        came_from = []
        open_split = []

        for sentence in self.f_analyzed_sentences:
            stanford_sentence = sentence.f_sentence
            actions = sentence.f_actions
            conjs = sentence.f_conjs
            processed = []
            for action in actions:
                if action.f_link and action.f_linkType == JUMP:
                    self.logger.info("Building Jump")
                    came_from = [action.f_link]
                    open_split = []
                    self.f_last_split = None
                    action.f_transient = True
                    continue
                if action not in processed:
                    flow = Flow(stanford_sentence)
                    conjoined = []
                    conj_type, conj_status = self.determine_conjunct_elements(conjs, action, conjoined, actions)
                    if len(conjoined) == 1:
                        self.handle_single_action(stanford_sentence, flow, conjoined[0], came_from, open_split)
                    elif len(conjoined) == 0:
                        flow.f_single = came_from[0]
                    else:
                        if conj_type in (OR, ANDOR) or Processing.has_frequency_attached(conjoined[0]):
                            self.create_dummy_node(came_from, flow)
                            flow_type = MULTIPLE_CHOICE if conj_type == ANDOR else CHOICE
                            self.build_gateway(came_from, open_split, stanford_sentence, processed, flow, conjoined, flow_type)
                        elif conj_type == AND:
                            if conj_status == ACTOR_SUBJECT:
                                self.create_dummy_node(came_from, flow)
                                self.build_gateway(came_from, open_split, stanford_sentence, processed, flow, conjoined, CONCURRENCY)
                            else:
                                if len(came_from) == 1:
                                    self.handle_single_action(stanford_sentence, flow, conjoined[0], came_from, open_split)
                                    processed.append(conjoined[0])
                                elif len(came_from) > 1:
                                    self.build_join(flow, came_from, conjoined[0])
                                    self.f_world.f_flows.append(flow)
                                else:
                                    came_from.append(conjoined[0])
                        elif conj_type == MIXED:
                            self.create_dummy_node(came_from, flow)
                            if len(came_from) > 1:
                                flow = self.join_with_dummy_node(came_from, stanford_sentence, flow)
                            self.handle_mixed_situation(stanford_sentence, flow, conjs, actions, came_from)
                            processed.extend(actions)

            for action in actions:
                link = action.f_link
                if link:
                    if action.f_linkType == FORWARD:
                        end = self.get_end(link)
                        if len(end) == 1:
                            came_from.append(end[0])
                    elif action.f_linkType == LOOP:
                        flow_in = self.find_flow(action, True)
                        flow_out = self.find_flow(action, False)
                        dummy_action = DummyAction(action)
                        self.f_world.f_actions.append(dummy_action)

                        if flow_in.f_direction == JOIN:
                            flow_in.f_single = dummy_action
                            flow_out.f_single = dummy_action
                            flow_out.f_multiples.append(action)
                            flow_out.f_type = CHOICE
                        else:
                            if flow_out:
                                flow_out.f_single = action
                            flow_in.f_multiples.append(dummy_action)
                            flow_in.f_type = CHOICE

                        if action in came_from:
                            came_from.remove(action)
                            came_from.append(dummy_action)

                        flow_in = self.find_flow(link, True)
                        if flow_in.f_direction == SPLIT:
                            dummy_action = DummyAction(action)
                            self.f_world.f_actions.append(dummy_action)
                            flow_in.f_multiples.append(dummy_action)
                            flow_in.f_multiples.remove(link)
                            new_flow = Flow(stanford_sentence)
                            new_flow.f_single = link
                            new_flow.f_multiples.append(dummy_action)
                            new_flow.f_multiples.append(action)
                            new_flow.f_type = CHOICE
                            new_flow.f_direction = JOIN
                            self.f_world.f_flows.append(new_flow)
                        else:
                            flow_in.f_multiples.append(action)

    def to_element(self, sentence_word_id):
        sentence_id, word_id = sentence_word_id
        sentence = self.f_raw_sentences[sentence_id]
        to_check = deepcopy(self.f_world.f_actions)

        for action in to_check:
            xcomp = action.f_xcomp
            if xcomp:
                to_check.append(xcomp)
        to_check.extend(self.f_world.get_actors_of_sentence(sentence))
        to_check.extend(self.f_world.get_resources_of_sentence(sentence))

        for el in to_check:
            if el.f_word_index == word_id:
                return el

        self.logger.error("Could not resolve the target of a manual resolution")
        return None

    @staticmethod
    def determine_animate_type(obj):
        if isinstance(obj, Resource) or obj.f_unreal:
            return INANIMATE
        elif Processing.object_pronoun(obj.f_name):
            return BOTH
        else:
            return ANIMATE

    def find_action(self, sentence_id, obj):
        if sentence_id < 0:
            return None

        sentence = self.f_raw_sentences[sentence_id]
        actions = self.f_world.get_actions_of_sentence(sentence)
        actions.sort(reverse=True)

        for action in actions:
            # TODO: why is this inside the loop?
            if sentence == obj.f_sentence:
                # Find last action that comes before the object
                if action.f_word_index < obj.f_word_index:
                    return action
            else:
                return action

        return self.find_action(sentence_id - 1, obj)

    def find_reference(self, sentence_id, obj, animate_type, is_cop):
        candidates = self.get_reference_candidates(sentence_id, obj, animate_type, is_cop)
        score = ROLE_MATCH_SCORE + (OBJECT_ROLE_SCORE if is_cop else SUBJECT_ROLE_SCORE)

        while sentence_id >= 0 and max(candidates.values()) < score:
            score -= SENTENCE_DISTANCE_PENALTY
            sentence_id -= 1
            new_candidates = self.get_reference_candidates(sentence_id, obj, animate_type, is_cop)
            if new_candidates:
                candidates.update(new_candidates)

        return self.get_max_score_elements(candidates)

    @staticmethod
    def can_be_merged(reference_action, action, only_share_props):
        if only_share_props or reference_action.f_negated == action.f_negated:
            if WordNetWrapper.is_weak_action(reference_action) or WordNetWrapper.is_weak_action(action):
                if reference_action.f_marker == action.f_marker:
                    if not reference_action.f_actorFrom or not action.f_actorFrom \
                            or reference_action.f_actorFrom.f_needsResolve \
                            or reference_action.f_actorFrom.f_metaActor \
                            or action.f_actorFrom.f_needsResolve \
                            or action.f_actorFrom.f_metaActor:
                        return not reference_action.f_object or not action.f_object \
                               or reference_action.f_object.f_needsResolve \
                               or action.f_object.f_needsResolve

        return False

    def merge(self, reference_action, action, param):
        pass

    def is_linkable(self, source, target):
        if not target:
            return False

        if source.f_baseForm == target.f_baseForm:
            if source.f_negated != target.f_negated:
                return False
            if source.f_cop and source.f_cop != target.f_cop:
                return False

            # If only one has an actor, returns false
            if source.f_actorFrom and target.f_actorFrom:
                source_actor = source.f_actorFrom
                if source_actor.f_needsResolve and isinstance(source_actor.f_reference, Actor):
                    source_actor = source_actor.f_reference

                target_actor = target.f_actorFrom
                if target_actor.f_needsResolve and isinstance(target_actor.f_reference, Actor):
                    target_actor = target_actor.f_reference

                if not self.ex_ob_equals(source_actor, target_actor):
                    return False
            elif source.f_actorFrom or target.f_actorFrom:
                return False

            # If only one has an object, returns false
            if source.f_object and target.f_object:
                source_object = source.f_object
                if source_object.f_needsResolve and isinstance(source_object, Actor):
                    source_object = source_object.f_reference

                target_object = target.f_object
                if target_object.f_needsResolve and isinstance(target_object, Actor):
                    target_object = target_object.f_reference

                if not self.ex_ob_equals(source_object, target_object):
                    return False
            elif source.f_object or target.f_object:
                return False

            if not source.f_xcomp and not target.f_xcomp:
                return self.check_specifier_equal(source, target, PP, [TO, ABOUT])
            elif source.f_xcomp:
                return self.is_linkable(source.f_xcomp, target.f_xcomp)
            else:
                return False

        else:
            return False

    def determine_link_type(self, source, target):
        if source.f_marker == IF:
            for spec in source.f_specifiers:
                for link in WordNetWrapper.get_accepted_forward_links():
                    if spec.f_name.find(link):
                        return FORWARD

            analyzed_sentence = self.f_analyzed_sentences[target.f_sentence.f_id]
            result = []
            conj_type, conj_status = self.determine_conjunct_elements(analyzed_sentence.f_conjs, target, result, analyzed_sentence.f_actions)
            if conj_type == OR or target.f_marker == IF or target.f_preAdvMod in f_sequenceIndicators:
                return JUMP
        else:
            if WordNetWrapper.is_AMOD_accepted_for_linking(source.f_mod):
                return LOOP

            to_check = source.get_specifiers(AMOD)
            if source.f_object:
                to_check.extend(source.f_object.get_specifiers(AMOD))
            for spec in to_check:
                if WordNetWrapper.is_AMOD_accepted_for_linking(spec.f_name):
                    return LOOP

        return NONE

    def determine_conjunct_elements(self, conjunctions, action, conjoined, actions):
        conj_type = None
        conjoined.append(action)
        status = NOT_CONTAINED

        for conj in conjunctions:
            if not conj_type or conj_type == conj.f_type:
                status = self.is_part_of(conj.f_from, conjoined)
                if status == NOT_CONTAINED:
                    status = self.is_part_of(conj.f_to, conjoined)
                if status != NOT_CONTAINED:
                    link = Search.get_action(conj.f_to, actions)
                    if link:
                        conjoined.append(link)
                        if not conj_type:
                            conj_type = conj.f_type
                    else:
                        self.logger.error("Unable to determine action from link {}".format(conj.f_to))
            elif conj_type:
                if conj_type == AND and status == ACTOR_OBJECT and conj.f_type != AND:
                    conj_type = MIXED

        return conj_type, status

    def handle_single_action(self, stanford_sentence, flow, param, came_from, open_split):
        pass

    def build_gateway(self, came_from, open_split, stanford_sentence, processed, flow, conjoined, flow_type):
        pass

    def create_dummy_node(self, came_from, flow):
        if len(came_from) == 0:
            dummy_action = DummyAction()
            self.f_world.f_actions.append(dummy_action)
            came_from.append(dummy_action)
            flow.f_single = dummy_action

    def build_join(self, flow, came_from, param):
        pass

    def join_with_dummy_node(self, came_from, stanford_sentence, flow):
        dummy_action = DummyAction(came_from[0])
        self.f_world.f_actions.append(dummy_action)
        self.build_join(flow, came_from, dummy_action)
        self.f_world.f_flows.append(flow)

        new_flow = Flow(stanford_sentence)
        new_flow.f_single = dummy_action
        return new_flow

    def handle_mixed_situation(self, stanford_sentence, flow, conjs, actions, came_from):
        pass

    def get_end(self, action):
        for flow in self.f_world.f_flows:
            if flow.f_direction == SPLIT:
                if flow.f_single == action:
                    return self.get_ends(flow.f_multiples)
            else:
                if action in flow.f_multiples:
                    return self.get_end(flow.f_single)

        return [action]

    def get_ends(self, multiples):
        result = []
        for action in multiples:
            if self.has_incoming_link(action, JUMP):
                result.extend(self.get_end(action))
            else:
                self.logger.info("Left out action, due to JUMP link")

        return result

    def find_flow(self, action, target):
        flows = self.f_world.f_flows
        flows.sort(reverse=True)
        for flow in flows:
            if target != (flow.f_direction == JOIN):
                if action in flow.f_multiples:
                    return flow
            else:
                if flow.f_single == action:
                    return flow

        return None

    @staticmethod
    def is_part_of(part, action_list):
        if isinstance(part, Action):
            return ACTION if part in action_list else NOT_CONTAINED

        for action in action_list:
            if action.f_actorFrom == part:
                return ACTOR_SUBJECT
            elif action.f_object == part:
                return ACTOR_OBJECT if isinstance(part, Actor) else RESOURCE

        return NOT_CONTAINED

    def get_reference_candidates(self, sentence_id, obj_to_check, animate_type, is_cop):
        if sentence_id < 0:
            return None

        sentence = self.f_raw_sentences[sentence_id]
        sentence_actors = self.f_world.get_actors_of_sentence(sentence)
        objects = []

        for actor in sentence_actors:
            if actor.f_metaActor:
                continue
            if animate_type == ANIMATE and actor.f_unreal:
                continue
            if animate_type == INANIMATE and not actor.f_unreal:
                continue
            objects.append(actor)

        if animate_type == INANIMATE:
            objects.extend(self.f_world.get_resources_of_sentence(sentence))

        objects.sort(reverse=True)
        candidates = {}

        for obj in objects:
            real_obj = obj
            if obj.f_needsResolve:
                if obj.f_reference and isinstance(obj.f_reference, ExtractedObject):
                    real_obj = obj.f_reference
                else:
                    continue
            if sentence == obj_to_check.f_sentence:
                if real_obj.f_word_index > obj_to_check.f_word_index:
                    continue

            score = (sentence_id - obj_to_check.f_sentence.f_id) * SENTENCE_DISTANCE_PENALTY

            if real_obj.f_subjectRole == (is_cop != obj_to_check.f_subjectRole):
                score += ROLE_MATCH_SCORE
            if not is_cop and real_obj.f_subjectRole:
                score += SUBJECT_ROLE_SCORE
            elif is_cop and not real_obj.f_subjectRole:
                score += OBJECT_ROLE_SCORE

            candidates[real_obj] = score

        return candidates

    @staticmethod
    def get_max_score_elements(candidates):
        max_score = None
        result = None

        for obj, score in candidates.items():
            if max_score:
                if score > max_score:
                    max_score = score
                    result = obj
                elif score == max_score:
                    if obj.f_sentence.f_id > result.f_sentence.f_id:
                        max_score = score
                        result = obj
                    elif obj.f_sentence.f_id == result.f_sentence.f_id and obj.f_word_index > result.f_word_index:
                        max_score = score
                        result = obj
            else:
                max_score = score
                result = obj

        return result

    def ex_ob_equals(self, source, target):
        if (source.f_name[-1] == "s") == (target.f_name[-1] == "s"):
            # TODO: check if necessary
            # String _name1 = WordNetWrapper.getBaseForm(_from1.getName(), false, POS.NOUN);
            # String _name2 = WordNetWrapper.getBaseForm(_from2.getName(), false, POS.NOUN);
            if source.f_name == target.f_name:
                if (source.f_determiner == NO) != (target.f_determiner == NO):
                    return False
            specifiers = [(AMOD, ""), (PP, FOR), (NN, ""), (NNAFTER, ""), (PP, ABOUT)]
            for spec in specifiers:
                if not self.check_specifier_equal(source, target, spec[0], spec[1]):
                    return False

            return True

        return False

    def check_specifier_equal(self, source, target, spec_type, head_word_for_unknowns):
        pass

    def has_incoming_link(self, target, link_type):
        for action in self.f_world.f_actions:
            if target == action.f_link:
                if not link_type or action.f_linkType == link_type:
                    return True

        return False
