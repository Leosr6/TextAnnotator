from copy import *
from core.CoreNLPWrapper import CoreNLPWrapper
from core.Base import Base
from data.WorldModel import WorldModel
from core.SentenceAnalyzer import SentenceAnalyzer
from data.StanfordSentence import StanfordSentence
from data.SentenceElements import *
from data.TextElements import *
from utils import Search, Processing
from utils.Constants import *


class TextAnalyzer(Base):

    def __init__(self):
        self.f_parser = CoreNLPWrapper()
        self.f_world = None
        self.f_text = ""
        self.f_analyzed_sentences = []
        self.f_raw_sentences = []
        self.f_reference_map = {}
        self.f_last_split = None

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
        # self.determine_links()
        self.build_flows()

        return self.f_world

    def create_stanford_sentences(self, text):

        # List of standford_sentences
        stanford_sentences = []

        sentences = self.f_parser.parse_text(text)

        for index, sentence in enumerate(sentences):
            tree, deps, raw_sentence = sentence
            s_sentence = StanfordSentence(tree, deps, raw_sentence, index)
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
        for analyzed_sentence in self.f_analyzed_sentences:
            stanford_sentence = analyzed_sentence.f_sentence
            deps = stanford_sentence.f_dependencies
            markers = Search.find_dependencies(deps, MARK)
            for dep in markers:
                action = self.find_node_action(dep['governor'], analyzed_sentence.f_actions, deps)
                if action:
                    value = dep['dependentGloss']
                    self.logger.debug("Marking {} with marker {}".format(action, value))
                    action.f_marker = value
                    action.f_markerPos = dep['dependent']

            markers = Search.find_dependencies(deps, ADVMOD)
            for dep in markers:
                action = self.find_node_action(dep['governor'], analyzed_sentence.f_actions, deps)
                if action and action.f_word_index > dep['dependent']:
                    value = dep['dependentGloss']
                    if value in f_parallelIndicators:
                        action.f_marker = WHILE
                        action.f_markerPos = dep['dependent']
                    elif value != ALSO:
                        self.logger.debug("Marking {} with advmod {}".format(action, value))
                        action.f_preAdvMod = value
                        action.f_preAdvModPos = dep['dependent']

            markers = Search.find_dependencies(deps, COMPLM)
            for dep in markers:
                if dep['dependentGloss'] != THAT:
                    action = self.find_node_action(dep['governor'], analyzed_sentence.f_actions, deps)
                    if action:
                        value = dep['dependentGloss']
                        if value in f_conditionIndicators:
                            value = IFCOMPLM
                        self.logger.debug("Marking {} with marker-complm {}".format(action, value))
                        action.f_marker = value
                        action.f_markerPos = dep['dependent']

        for analyzed_sentence in self.f_analyzed_sentences:
            stanford_sentence = analyzed_sentence.f_sentence
            for action in self.f_world.get_actions_of_sentence(stanford_sentence):
                specs = action.get_specifiers(PP)
                if action.f_object:
                    specs.extend(action.f_object.get_specifiers(PP))
                specs.extend(action.get_specifiers(RCMOD))
                specs.extend(action.get_specifiers(SBAR))

                for spec in specs:
                    if Search.starts_with(f_conditionIndicators, spec.f_name) and not action.f_marker:
                        self.logger.debug("Marking {} with marker {} if".format(action, spec.f_name))
                        action.f_marker = IF
                        action.f_markerPos = spec.f_word_index
                        action.realMarker = spec.f_name
                        if spec.f_name not in f_conditionIndicators:
                            action.f_markerFromPP = True

                    for indic in f_sequenceIndicators:
                        if spec.f_name.startswith(indic) and not action.f_preAdvMod:
                            action.f_preAdvMod = indic
                            action.f_preAdvModPos = spec.f_word_index
                            action.preAdvModFromSpec = True

                    if spec.f_name in f_parallelIndicators and not action.f_marker:
                        self.logger.debug("Marking {} with marker {} while".format(action, spec.f_name))
                        action.f_marker = WHILE
                        action.f_markerPos = spec.f_word_index
                        action.realMarker = spec.f_name

        for analyzed_sentence in self.f_analyzed_sentences:
            stanford_sentence = analyzed_sentence.f_sentence
            linked = []
            next_mark = None
            actions = self.f_world.get_actions_of_sentence(stanford_sentence)
            for action in actions:
                if next_mark and not action.f_preAdvMod:
                    action.f_preAdvMod = next_mark
                    action.f_preAdvModPos = -1
                    self.logger.debug("Marking {} with implicit advmod {}".format(action, next_mark))
                if action in linked:
                    next_mark = None
                if (action.f_marker in f_conditionIndicators and not action.f_markerFromPP) or action.f_preAdvMod in f_conditionIndicators:
                    next_mark = THEN
                    self.determine_conjunct_elements(copy(analyzed_sentence.f_conjs), action, linked, actions)

        for analyzed_sentence in self.f_analyzed_sentences:
            actions = analyzed_sentence.f_actions
            for action in actions:
                linked = []
                self.determine_conjunct_elements(copy(analyzed_sentence.f_conjs), action, linked, actions)
                if len(linked) > 1:
                    for linked_action in linked:
                        if not linked_action.f_preAdvMod:
                            linked_action.f_preAdvMod = action.f_preAdvMod
                            linked_action.f_preAdvModPos = -1
                        if not linked_action.f_marker and action.f_marker:
                            if Search.starts_with(finishedIndicators, action.f_marker):
                                linked_action.f_marker = action.f_marker
                                linked_action.f_markerPos = action.f_markerPos

        for analyzed_sentence in self.f_analyzed_sentences:
            actions = analyzed_sentence.f_actions
            for index, action in enumerate(actions):
                if action.f_marker == IFCOMPLM:
                    action.f_marker = IF
                elif action.f_marker == IF:
                    if index > 0:
                        previous_action = actions[index - 1]
                        actions[index - 1] = action
                        actions[index] = previous_action
                        self.f_world.switch_actions(action, previous_action)
                    break

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
        actions = list(reversed(self.f_world.f_actions))
        for first_index in range(len(actions) - 1):
            for second_index in range(first_index + 1, len(actions)):
                first_action, second_action = actions[first_index], actions[second_index]
                if self.is_linkable(first_action, second_action):
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
            conjs = copy(sentence.f_conjs)
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
                    else:
                        if len(came_from) > 0:
                            flow.f_single = came_from[0]
                        if conj_type in (OR, XOR) or Processing.has_frequency_attached(conjoined[0]):
                            self.create_dummy_node(came_from, flow)
                            flow_type = MULTIPLE_CHOICE if conj_type == OR else CHOICE
                            self.build_gateway(came_from, open_split, stanford_sentence, processed, flow, conjoined, flow_type)
                        elif conj_type == AND:
                            if conj_status == ACTOR_SUBJECT:
                                self.create_dummy_node(came_from, flow)
                                self.build_gateway(came_from, open_split, stanford_sentence, processed, flow, conjoined, CONCURRENCY)
                            else:
                                if len(came_from) > 1:
                                    self.build_join(flow, came_from, conjoined[0])
                                    self.f_world.add_flow(flow)
                                else:
                                    self.handle_single_action(stanford_sentence, flow, conjoined[0], came_from, open_split)
                                    processed.append(conjoined[0])
                        elif conj_type == MIXED:
                            self.create_dummy_node(came_from, flow)
                            if len(came_from) > 1:
                                flow = self.join_with_dummy_node(came_from, stanford_sentence, flow)
                            self.handle_mixed_situation(stanford_sentence, flow, sentence.f_conjs, actions, came_from)
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
                        self.f_world.add_action(dummy_action)

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
                            self.f_world.add_action(dummy_action)
                            flow_in.f_multiples.append(dummy_action)
                            flow_in.f_multiples.remove(link)
                            new_flow = Flow(stanford_sentence)
                            new_flow.f_single = link
                            new_flow.f_multiples.append(dummy_action)
                            new_flow.f_multiples.append(action)
                            new_flow.f_type = CHOICE
                            new_flow.f_direction = JOIN
                            self.f_world.add_flow(new_flow)
                        else:
                            flow_in.f_multiples.append(action)

        # When the text ends in a SPLIT, we must create a JOIN for it
        came_from.extend(open_split)
        if len(came_from) > 1:
            dummy_flow = Flow(stanford_sentence)
            dummy_action = DummyAction(action)
            self.f_world.add_action(dummy_action)
            self.build_join(dummy_flow, came_from, dummy_action)
            self.f_world.add_flow(dummy_flow)

    def to_element(self, sentence_word_id):
        sentence_id, word_id = sentence_word_id
        sentence = self.f_raw_sentences[sentence_id]
        to_check = copy(self.f_world.f_actions)

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
        elif Processing.can_be_object_pronoun(obj.f_name):
            return BOTH
        else:
            return ANIMATE

    def find_action(self, sentence_id, obj):
        if sentence_id < 0:
            return None

        sentence = self.f_raw_sentences[sentence_id]
        actions = reversed(self.f_world.get_actions_of_sentence(sentence))

        for action in actions:
            if sentence == obj.f_sentence:
                # Find last action that comes before the object
                if action.f_word_index < obj.f_word_index:
                    return action
            else:
                # Returns the last action of the previous sentence
                return action

        return self.find_action(sentence_id - 1, obj)

    def find_reference(self, sentence_id, obj, animate_type, is_cop):
        candidates = self.get_reference_candidates(sentence_id, obj, animate_type, is_cop)
        min_score = ROLE_MATCH_SCORE + (OBJECT_ROLE_SCORE if is_cop else SUBJECT_ROLE_SCORE)
        scores = candidates.values()

        while sentence_id >= 0 and (len(scores) == 0 or max(scores) < min_score):
            min_score -= SENTENCE_DISTANCE_PENALTY
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

    def merge(self, reference_action, action, copy_only):
        # Define main and merge actions
        if WordNetWrapper.is_weak_action(reference_action):
            merge_action = reference_action
            main_action = action
        else:
            merge_action = action
            main_action = reference_action

        # Copy actor from
        if merge_action.f_actorFrom:
            if not main_action.f_actorFrom:
                actor_from = None
                if not merge_action.f_actorFrom.f_needsResolve:
                    actor_from = merge_action.f_actorFrom
                elif isinstance(merge_action.f_actorFrom.f_reference, Actor):
                    actor_from = merge_action.f_actorFrom.f_reference

                if actor_from:
                    main_action.f_actorFrom = actor_from
            elif main_action.f_actorFrom.f_needsResolve and not merge_action.f_actorFrom.f_needsResolve:
                main_action.f_actorFrom = merge_action.f_actorFrom

        # Copy object
        if not main_action.f_object or main_action.f_object.f_needsResolve:
            if merge_action.f_object and not merge_action.f_object.f_needsResolve:
                main_action.f_object = merge_action.f_object

        # Copy specs
        for spec in merge_action.get_specifiers(PP):
            main_action.f_specifiers.append(spec)

        if not copy_only:
            for analyzed_sentence in self.f_analyzed_sentences:
                if merge_action in analyzed_sentence.f_actions:
                    analyzed_sentence.f_actions.remove(merge_action)
            self.f_world.f_actions.remove(merge_action)

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
                return self.specifier_equal_list(source, target, PP, [TO, ABOUT])
            elif source.f_xcomp:
                return self.is_linkable(source.f_xcomp, target.f_xcomp)
            else:
                return False

        else:
            return False

    def determine_link_type(self, source, target):
        if source.f_marker == IF:
            for spec in source.f_specifiers:
                for link in WordNetWrapper.accepted_forward_links:
                    if spec.f_name.find(link):
                        return FORWARD

            analyzed_sentence = self.f_analyzed_sentences[target.f_sentence.f_id]
            result = []
            conj_type, conj_status = self.determine_conjunct_elements(copy(analyzed_sentence.f_conjs), target, result, analyzed_sentence.f_actions)
            if conj_type == OR or target.f_marker == IF or target.f_preAdvMod in f_sequenceIndicators:
                return JUMP
        else:
            if source.f_mod in WordNetWrapper.accepted_AMOD_list:
                return LOOP

            to_check = source.get_specifiers(AMOD)
            if source.f_object:
                to_check.extend(source.f_object.get_specifiers(AMOD))
            for spec in to_check:
                if spec.f_name in WordNetWrapper.accepted_AMOD_list:
                    return LOOP

        return NONE

    def determine_conjunct_elements(self, conjunctions, action, conjoined, actions):
        conj_type = None
        conj_status = NOT_CONTAINED
        conjoined.append(action)
        conjs_used = []

        for conj in conjunctions:
            if not conj_type or conj_type == conj.f_type:
                status = self.is_part_of(conj.f_from, conjoined)
                target = conj.f_to
                if status == NOT_CONTAINED:
                    status = self.is_part_of(conj.f_to, conjoined)
                    target = conj.f_from
                if status != NOT_CONTAINED and conj_status in (NOT_CONTAINED, status):
                    link = Search.get_action(actions, target)
                    if link:
                        if link not in conjoined:
                            conjoined.append(link)
                            conjs_used.append(conj)
                            if not conj_type:
                                conj_status = status
                                conj_type = conj.f_type
                    else:
                        self.logger.error("Unable to determine action from link {}".format(conj.f_to))
            # elif conj_type:
            #     if conj_type == AND and conj_status == ACTOR_SUBJECT and conj.f_type != AND:
            #         conj_type = MIXED

        for conj in conjs_used:
            conjunctions.remove(conj)

        return conj_type, conj_status

    def handle_single_action(self, stanford_sentence, flow, action, came_from, open_split):
        if action.f_marker != IF and action.f_preAdvMod != OTHERWISE and action.f_preAdvMod not in f_sequenceIndicators and len(open_split) > 0:
            came_from.extend(open_split)
            self.clear_split(open_split)

        if len(came_from) == 0:
            self.create_dummy_node(came_from, flow)
        if len(came_from) >= 1:
            last_flow_added = self.f_world.f_lastFlowAdded

            if last_flow_added:
                open_parallel = last_flow_added.f_type == CONCURRENCY and last_flow_added.f_direction == SPLIT
                open_while = last_flow_added.f_multiples[0].f_marker == WHILE and last_flow_added.f_direction == SPLIT
                new_sentence = came_from[-1].f_sentence != action.f_sentence

                if action.f_marker == WHILE and not open_parallel and new_sentence:
                    flow.f_single = came_from[0]
                    flow.f_multiples.append(action)
                    flow.f_type = CONCURRENCY
                    self.f_world.add_flow(flow)
                    came_from.clear()
                    came_from.append(action)
                    return
                if action.f_marker == WHILE or (open_while and not new_sentence):
                    last_flow_added.f_multiples.append(action)
                    last_flow_added.f_type = CONCURRENCY
                    came_from.append(action)
                    return

            if len(came_from) > 1:
                dummy_flow = Flow(stanford_sentence)
                dummy_action = DummyAction(action)
                self.f_world.add_action(dummy_action)
                self.build_join(dummy_flow, came_from, dummy_action)
                self.clear_split(open_split)
                self.f_world.add_flow(dummy_flow)

            if action.f_marker in (WHEREAS, IF) or action.f_preAdvMod == OTHERWISE:
                if self.f_last_split or action.f_marker != IF:
                    if not self.f_last_split:
                        self.f_last_split = self.f_world.f_lastFlowAdded
                    open_split.clear()
                    open_split.extend(self.get_ends(self.f_last_split.f_multiples))
                    self.f_last_split.f_multiples.append(action)
                    came_from.clear()
                    came_from.append(action)
                    if action.f_marker == WHEREAS:
                        came_from.extend(open_split)
                        self.clear_split(open_split)
                    return
                flow.f_type = CHOICE
                self.f_last_split = flow

                flow.f_single = came_from[0]
                flow.f_multiples = [action]
                came_from.clear()
                came_from.append(action)
            else:
                flow.f_type = SEQUENCE
                flow.f_single = came_from[0]
                flow.f_multiples = [action]
                came_from.clear()
                came_from.append(action)
                if action.f_preAdvMod not in f_sequenceIndicators:
                    self.clear_split(open_split)

            self.f_world.add_flow(flow)

    def clear_split(self, open_split):
        open_split.clear()
        self.f_last_split = None

    def build_gateway(self, came_from, open_split, stanford_sentence, processed, flow, gateway_actions, flow_type):
        first_action = gateway_actions[0]
        if first_action.f_marker == IF or first_action.f_preAdvMod == OTHERWISE or first_action.f_preAdvMod in f_sequenceIndicators:
            if first_action.f_preAdvMod not in f_sequenceIndicators:
                open_split.clear()
            if self.f_last_split:
                dummy_action = DummyAction(first_action)
                self.f_world.add_action(dummy_action)
                open_split.extend(self.get_ends(self.f_last_split.f_multiples))
                self.f_last_split.f_multiples.append(dummy_action)
                came_from.clear()
                came_from.append(dummy_action)
                flow.f_single = dummy_action
            if first_action == OTHERWISE:
                came_from.extend(open_split)
                self.clear_split(open_split)
        else:
            came_from.extend(open_split)
            self.clear_split(open_split)

        if len(came_from) > 1:
            flow = self.join_with_dummy_node(came_from, stanford_sentence, flow)

        flow.f_multiples = gateway_actions
        flow.f_type = flow_type
        came_from.clear()

        for action in gateway_actions:
            if not self.has_incoming_link(action, JUMP):
                came_from.append(action)
            else:
                self.logger.info("Left out action, due to JUMP link")

        if len(came_from) == 0:
            dummy_action = DummyAction(first_action)
            self.f_world.add_action(dummy_action)
            flow.f_multiples.append(dummy_action)
            came_from.append(dummy_action)

        processed.extend(gateway_actions)
        self.f_world.add_flow(flow)

    def create_dummy_node(self, came_from, flow):
        if len(came_from) == 0:
            dummy_action = DummyAction()
            self.f_world.add_action(dummy_action)
            came_from.append(dummy_action)
            flow.f_single = dummy_action

    def build_join(self, flow, came_from, action):
        flow.f_direction = JOIN
        flow.f_single = action
        flow.f_multiples = copy(came_from)
        other_flow = self.find_split(came_from[0])
        if other_flow:
            flow.f_type = other_flow.f_type
        came_from.clear()
        came_from.append(action)

    def find_split(self, action):
        flow = self.find_flow(action, True)
        if flow and flow.f_direction == SPLIT:
            if flow.f_type != SEQUENCE:
                return flow
            else:
                return self.find_split(flow.f_single)
        return None

    def join_with_dummy_node(self, came_from, stanford_sentence, flow):
        dummy_action = DummyAction(came_from[0])
        self.f_world.add_action(dummy_action)
        self.build_join(flow, came_from, dummy_action)
        self.f_world.add_flow(flow)

        new_flow = Flow(stanford_sentence)
        new_flow.f_single = dummy_action
        return new_flow

    def handle_mixed_situation(self, stanford_sentence, flow, conjs, all_actions, came_from):
        actors = set()
        for conj in copy(conjs):
            if conj.f_type == AND:
                if isinstance(conj.f_from, Actor):
                    actors.add(conj.f_from)
                if isinstance(conj.f_to, Actor):
                    actors.add(conj.f_to)
                conjs.remove(conj)

        exits = []
        entries = []

        for actor in actors:
            actions = [action for action in all_actions if action.f_actorFrom == actor]
            dummy_start = DummyAction(actions[0])
            dummy_end = DummyAction(actions[0])
            self.f_world.add_action(dummy_start)
            self.f_world.add_action(dummy_end)
            entries.append(dummy_start)
            exits.append(dummy_end)
            self.build_block(stanford_sentence, dummy_start, dummy_end, actions, conjs)

        flow.f_multiples = entries
        flow.f_type = CONCURRENCY
        self.f_world.add_flow(flow)

        dummy_action = DummyAction(all_actions[0])
        self.f_world.add_action(dummy_action)

        join = Flow(stanford_sentence)
        join.f_multiples = exits
        join.f_type = CONCURRENCY
        join.f_single = dummy_action
        join.f_direction = JOIN
        self.f_world.add_flow(join)

        came_from.clear()
        came_from.append(dummy_action)

    def build_block(self, stanford_sentence, start, end, actions, conjs):
        split = Flow(stanford_sentence)
        join = Flow(stanford_sentence)

        join.f_direction = JOIN
        split.f_single = start
        join.f_single = end

        if conjs[0].f_type == OR:
            split.f_type = MULTIPLE_CHOICE
            join.f_type = MULTIPLE_CHOICE
        else:
            split.f_type = CHOICE
            join.f_type = CHOICE

        split.f_multiples = actions
        join.f_multiples = actions
        self.f_world.add_flow(split)
        self.f_world.add_flow(join)

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
            if not self.has_incoming_link(action, JUMP):
                result.extend(self.get_end(action))
            else:
                self.logger.info("Left out action, due to JUMP link")

        return result

    def find_flow(self, action, target):
        flows = reversed(self.f_world.f_flows)
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

        if animate_type != ANIMATE:
            objects.extend(self.f_world.get_resources_of_sentence(sentence))

        objects = reversed(objects)
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
        if source.f_name.endswith("s") == target.f_name.endswith("s"):
            source_base = WordNetWrapper.get_base_form(source.f_name, False, POS_NOUN)
            target_base = WordNetWrapper.get_base_form(target.f_name, False, POS_NOUN)
            if source_base == target_base:
                if (source.f_determiner == NO) != (target.f_determiner == NO):
                    return False
            specifiers = [(AMOD, ""), (PP, FOR), (NN, ""), (NNAFTER, ""), (PP, ABOUT)]
            for spec in specifiers:
                if not self.check_specifier_equal(source, target, spec[0], spec[1]):
                    return False

            return True

        return False

    @staticmethod
    def specifier_equal_list(source, target, spec_type, words_unknowns):
        for source_spec in source.get_specifiers(spec_type):
            if source_spec.f_pt in (CORE, GENITIVE) or \
                    (source_spec.f_pt == UNKNOWN and words_unknowns and source_spec.f_headWord in words_unknowns):
                if source_spec.f_name not in WordNetWrapper.accepted_AMOD_list:
                    found_spec = False
                    for target_spec in target.get_specifiers(spec_type):
                        if source_spec.f_name == target_spec.f_name:
                            found_spec = True
                            break
                    if not found_spec:
                        return False

        return True

    @staticmethod
    def check_specifier_equal(source, target, spec_type, head_word):
        for source_spec in source.get_specifiers(spec_type):
            if head_word and head_word != source_spec.f_headWord:
                continue
            if source_spec.f_name not in WordNetWrapper.accepted_AMOD_list:
                found_spec = False
                for target_spec in target.get_specifiers(spec_type):
                    if source_spec.f_name == target_spec.f_name:
                        found_spec = True
                        break
                if not found_spec:
                    return False

        return True

    def has_incoming_link(self, target, link_type):
        for action in self.f_world.f_actions:
            if target == action.f_link:
                if not link_type or action.f_linkType == link_type:
                    return True

        return False

    def find_node_action(self, dep_index, action_list, deps):
        for action in action_list:
            if action.f_word_index == dep_index:
                return action

        cops = Search.find_dependencies(deps, COP)
        for dep in cops:
            if dep['governor'] == dep_index:
                return self.find_node_action(dep['dependent'], action_list, deps)

        return None
