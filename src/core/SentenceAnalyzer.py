from copy import *
from core.Base import Base
from core.ElementsBuilder import ElementsBuilder as Builder
from data.AnalyzedSentence import AnalyzedSentence
from data.SentenceElements import *
from utils import Search
from utils.Constants import *


class SentenceAnalyzer(Base):

    def __init__(self, world_model):
        self.f_world = world_model
        self.f_sentenceTags = [S, SBAR, SINV]
        self.f_dependencies = []
        self.f_analyzed_sentence = None
        self.f_full_sentence = None
        self.f_stanford_sentence = None
        self.f_ignore_np_subsentences = False

    def analyze_sentence(self, sentence):

        self.f_stanford_sentence = sentence
        self.f_full_sentence = sentence.f_tree
        self.f_dependencies = sentence.f_dependencies
        self.f_analyzed_sentence = AnalyzedSentence(sentence, sentence.f_tree)

        dependencies = sentence.f_dependencies
        main_sentence = sentence.f_tree[0]

        self.analyze_recursive(main_sentence, dependencies)
        self.check_global_conjunctions()

        actions = self.f_analyzed_sentence.f_actions
        actions.sort(key=lambda a: a.f_word_index)

        for action in actions:
            self.f_world.add_action(action)

        self.logger.debug("Extracted actions {}".format(actions))

        return self.f_analyzed_sentence

    def analyze_recursive(self, main_sentence, dependencies):

        main_sentence = deepcopy(main_sentence)
        sub_sentence_count = self.determine_sub_sentence_count(main_sentence)

        if sub_sentence_count == 0:
            self.extract_elements(main_sentence, dependencies)
        elif sub_sentence_count == 1:
            sub_sentence = self.find_sub_sentences(main_sentence)[0]
            filtered_dependencies = self.filter_dependencies(sub_sentence,
                                                             dependencies)
            self.analyze_recursive(sub_sentence, filtered_dependencies)

            sub_sentence_index = sub_sentence.treeposition()
            del(main_sentence[sub_sentence_index])
            deps = [dep for dep in dependencies if dep['dep'] == RCMOD or dep not in filtered_dependencies]
            if len(Search.find_dependencies(deps, (NSUBJ, AGENT, NSUBJPASS, DOBJ))) > 0:
                self.extract_elements(main_sentence, deps)

        else:
            sub_sentences = self.find_sub_sentences(main_sentence)
            for sub_sentence in sub_sentences:
                filtered_dependencies = self.filter_dependencies(sub_sentence,
                                                                 dependencies)
                self.analyze_recursive(sub_sentence, filtered_dependencies)

    def filter_dependencies(self, sentence, dependencies):
        filtered_deps = []
        start_index = Search.find_sentence_index(self.f_full_sentence, sentence)
        end_index = start_index + len(sentence.leaves())

        for dep in dependencies:
            if dep['dep'] == RCMOD or \
                    (start_index <= dep['governor'] <= end_index
                     and start_index <= dep['dependent'] <= end_index):
                filtered_deps.append(dep)

        return filtered_deps

    def extract_elements(self, sentence, dependencies):

        active = self.is_active_sentence(sentence, dependencies)
        actors = self.determine_subjects(sentence, dependencies, active)
        verbs = self.determine_verbs(sentence, dependencies, active)
        verbs = self.remove_examples(verbs)

        actions = []
        all_objects = []

        # Creating actions from verbs
        for verb in verbs:
            objects = self.determine_object(sentence, verb, dependencies, active)
            self.filter_verb(verb, actors, objects)
            all_objects.extend(objects)

            if len(objects) > 0:
                # One verb can generate multiple actions
                for el in objects:
                    new_action = copy(verb)
                    new_action.f_object = el
                    actions.append(new_action)
            else:
                actions.append(verb)

        final_actions = []

        # Combining actors with actions
        if len(actors) > 0:
            for actor in actors:
                for action in actions:
                    new_action = copy(action)
                    new_action.f_actorFrom = actor
                    final_actions.append(new_action)
        else:
            final_actions = actions

        # Add everything to the world model

        for actor in actors:
            self.f_world.add_actor(actor)

        for el in all_objects:
            if isinstance(el, Actor):
                self.f_world.add_actor(el)
            else:
                self.f_world.add_resource(el)

        for action in final_actions:
            self.f_analyzed_sentence.f_actions.append(action)
            if action.f_xcomp:
                actor_from = action.f_xcomp.f_actorFrom
                obj = action.f_xcomp.f_object
                if actor_from:
                    self.f_world.add_actor(actor_from)
                if obj:
                    if isinstance(obj, Actor):
                        self.f_world.add_actor(obj)
                    else:
                        self.f_world.add_resource(obj)

    def filter_verb(self, verb, actors, objects):
        to_check = []
        spec_to_check = []

        to_check.extend(actors)
        to_check.extend(objects)

        spec_to_check.extend(verb.get_specifiers((PP, DOBJ, RCMOD)))

        for el in to_check:
            for spec in spec_to_check:
                if spec.f_word_index == el.f_word_index:
                    self.logger.debug("Removing specifier: {}".format(spec))
                    verb.f_specifiers.remove(spec)

            if verb.f_cop and verb.f_cop == el.f_name:
                self.logger.debug("Removing cop: {}".format(verb.f_cop))
                verb.f_cop = None
                verb.f_copIndex = -1
                for obj_spec in el.get_specifiers((PP,)):
                    for spec in spec_to_check:
                        if spec.f_name == obj_spec.f_name:
                            self.logger.debug("Removing cop-specifier: {}".format(spec.f_name))
                            verb.f_specifiers.remove(spec)

        to_check = []
        spec_to_check = []

        to_check.extend(self.f_analyzed_sentence.f_actions)
        spec_to_check.extend(verb.get_specifiers((SBAR,)))

        for spec in spec_to_check:
            start_index = spec.f_word_index
            end_index = start_index + len(spec.f_name.split(" "))
            for el in to_check:
                if start_index <= el.f_word_index < end_index:
                    verb.f_specifiers.remove(spec)
                    break

        self.logger.debug("Filtered verb {}".format(verb))

    def is_active_sentence(self, sentence, dependencies):
        subj = Search.find_dependencies(dependencies, (NSUBJ, CSUBJ, DOBJ))
        subj = self.exclude_relative_clauses(sentence, subj)
        if len(subj) > 0:
            return True

        subj_pass = Search.find_dependencies(dependencies, (NSUBJPASS,
                                                            CSUBJPASS,
                                                            AGENT))
        subj_pass = self.exclude_relative_clauses(sentence, subj_pass)
        if len(subj_pass) > 0:
            return False

        self.logger.debug("It is not clear whether this sentence is active or passive!")
        return False

    """ Extract the subjects of the activity
        Subjects are equivalent to Actors
        It's possible that a sentence has no actor
        For example: passive sentence and relative pronouns
    """

    def determine_subjects(self, sentence, dependencies, active):
        actors = []

        main_actor_index = None

        # Find main actor

        subj = Search.find_dependencies(dependencies, NSUBJ) if active else \
            Search.find_dependencies(dependencies, AGENT)

        subj = self.exclude_relative_clauses(sentence, subj)
        if len(subj) == 0:
            self.logger.debug("Sentence contains no subject!")
        elif len(subj) == 1:
            main_actor_index = subj[0]['dependent']
        else:
            self.logger.info("Sentence has more then one subject")
            self.logger.debug(subj)

        # Find all actors

        if main_actor_index:
            actor = Builder.create_actor(self.f_stanford_sentence,
                                         self.f_full_sentence,
                                         main_actor_index, dependencies)
            actor.f_subjectRole = True
            actor.f_passive = not active
            actors.append(actor)
            for new_actor in self.check_conjunctions(dependencies, actor, True, True, active):
                new_actor.f_subjectRole = True
                new_actor.f_passive = not active
                actors.append(new_actor)

        return actors

    def determine_verbs(self, sentence, dependencies, active):
        actions = []

        main_predicate_index = None

        # Determine main predicate

        if active:
            nsubj = Search.find_dependencies(dependencies, NSUBJ)
            nsubj = self.exclude_relative_clauses(sentence, nsubj)
            if len(nsubj) == 0:
                dobj = Search.find_dependencies(dependencies, DOBJ)
                dobj = self.exclude_relative_clauses(sentence, dobj)
                if len(dobj) >= 1:
                    main_predicate_index = dobj[0]['governor']
            elif len(nsubj) == 1:
                main_predicate_index = nsubj[0]['governor']
                cop = Search.find_dependencies(dependencies, COP)
                cop = self.exclude_relative_clauses(sentence, cop)
                for dep in cop:
                    if dep['governor'] == main_predicate_index:
                        main_predicate_index = dep['dependent']
                        break
            else:
                self.logger.info("Sentence has more than one active predicate")
                self.logger.debug(nsubj)

        else:
            nsubjpass = Search.find_dependencies(dependencies, NSUBJPASS)
            nsubjpass = self.exclude_relative_clauses(sentence, nsubjpass)
            if len(nsubjpass) == 1:
                main_predicate_index = nsubjpass[0]['governor']
            elif len(nsubjpass) > 1:
                self.logger.info("Sentence has more than one passive predicate")
                self.logger.debug(nsubjpass)

        # Find all actions

        if main_predicate_index:
            main_predicate = Search.find_dep_in_tree(self.f_full_sentence,
                                                     main_predicate_index)
            vp_head = Search.get_full_phrase_tree(main_predicate, VP)
            action = Builder.create_action(self.f_stanford_sentence, self.f_full_sentence,
                                           main_predicate_index, dependencies, active)
            self.check_sub_sentences(vp_head, dependencies, action, False)
            actions.append(action)
        else:
            verbs = Search.find_in_tree(sentence, VP, (SBAR, S))
            if len(verbs) == 0:
                self.logger.info("Sentence contains no action")
            elif len(verbs) > 1:
                self.logger.info("Sentence has more than one verb phrase")
            else:
                vp = verbs[0]
                action = Builder.create_action_syntax(self.f_stanford_sentence, self.f_full_sentence, vp)
                self.check_sub_sentences(vp, dependencies, action, False)
                actions.append(action)

        if len(actions) > 0:
            for new_action in self.check_conjunctions(dependencies, actions[0],
                                                      False, False, active):
                actions.append(new_action)

        return actions

    def determine_object(self, sentence, verb, dependencies, active):
        objects = []

        if verb.f_xcomp:
            xcomp_obj = self.determine_object(sentence, verb.f_xcomp, dependencies, active)
            if len(xcomp_obj) > 0:
                verb.f_xcomp.f_object = xcomp_obj[0]

        if not active:
            nsubjpass = Search.find_dependencies(dependencies, NSUBJPASS)
            nsubjpass = self.exclude_relative_clauses(sentence, nsubjpass)
            if len(nsubjpass) == 0:
                objs = self.determine_object_from_dobj(verb, dependencies)
                objects.extend(objs)
            else:
                if len(nsubjpass) > 1:
                    self.logger.debug("Passive sentence with more than one subject!")
                dep_index = nsubjpass[0]['dependent']
                obj = Builder.create_object(self.f_stanford_sentence, self.f_full_sentence, dep_index, dependencies)
                obj.f_subjectRole = True
                objects.append(obj)
                self.check_np_sub_sentences(dep_index, dependencies, obj)
        else:
            objs = self.determine_object_from_dobj(verb, dependencies)
            objects.extend(objs)

        if len(objects) > 0:
            conjs = self.check_conjunctions(dependencies, objects[0], True, False, active)
            for conj in conjs:
                if isinstance(conj, Element):
                    objects.append(conj)

        return objects

    def determine_object_from_dobj(self, verb, dependencies):

        objects = []

        dobjs = Search.find_dependencies(dependencies, DOBJ)
        dobjs_filtered = Search.filter_by_gov(dobjs, verb)

        if len(dobjs_filtered) == 0:
            if not verb.f_xcomp or not verb.f_xcomp.f_object:
                for conj in self.f_analyzed_sentence.f_conjs:
                    if conj.f_to == verb:
                        dobjs_filtered = [dep for dep in dobjs if conj.f_to.f_word_index < dep['dependent']]
                    else:
                        dobjs_filtered = [dep for dep in dobjs if conj.f_from.f_word_index < dep['dependent']]

        if len(dobjs_filtered) == 0:
            preps = Search.find_dependencies(dependencies, PREP)
            preps_filtered = []
            for dep in preps:
                if dep['governorGloss'] in verb.f_name \
                        and dep['governor'] > verb.f_word_index:
                    preps_filtered.append(dep)

            if len(preps_filtered) == 0:
                cops = Search.find_dependencies(dependencies, COP)
                if len(cops) == 0:
                    self.logger.debug("No Object found")
                elif len(cops) > 1:
                    self.logger.info("Sentence with more than one copula object!")
                    self.logger.debug(cops)
                else:
                    dep_index = cops[0]['governor']
                    dep_in_tree = Search.find_dep_in_tree(self.f_full_sentence, dep_index)
                    if dep_in_tree.parent().label() == NP:
                        obj = Builder.create_object(self.f_stanford_sentence, self.f_full_sentence, dep_index, dependencies)
                        objects.append(obj)
                        self.check_np_sub_sentences(dep_index, dependencies, obj)
                    else:
                        self.logger.debug("No object found")
            elif len(preps_filtered) > 1:
                self.logger.info("Sentence with more than one prepositional object!")
                self.logger.debug(preps_filtered)
            else:
                dep_index = preps_filtered[0]['dependent']
                dep_in_tree = Search.find_dep_in_tree(self.f_full_sentence, dep_index)
                if dep_in_tree.parent().label() == NP:
                    obj = Builder.create_object(self.f_stanford_sentence, self.f_full_sentence, dep_index, dependencies)
                    objects.append(obj)
                    self.check_np_sub_sentences(dep_index, dependencies, obj)
                else:
                    self.logger.debug("No object found")
        else:
            dep_index = dobjs_filtered[0]['dependent']
            obj = Builder.create_object(self.f_stanford_sentence, self.f_full_sentence, dep_index, dependencies)
            objects.append(obj)
            self.check_np_sub_sentences(dep_index, dependencies, obj)

        return objects

    def exclude_relative_clauses(self, sentence, dependencies):

        relative_clauses = []

        for dep in dependencies:
            if dep['dep'] != RCMOD:
                sentence_index = Search.find_sentence_index(self.f_full_sentence,
                                                            sentence)
                dep_in_tree = Search.find_dep_in_tree(self.f_full_sentence,
                                                      dep['dependent'])

                while dep_in_tree.label() != ROOT:

                    if sentence.label() == dep_in_tree.label():
                        part_index = Search.find_sentence_index(self.f_full_sentence,
                                                                dep_in_tree)
                        if sentence_index >= part_index:
                            break

                    if dep_in_tree.label() in (SBAR, S, PRN) and dep_in_tree.parent().label() != SBAR:
                        relative_clauses.append(dep)
                        break

                    dep_in_tree = dep_in_tree.parent()

        return [dep for dep in dependencies if dep not in relative_clauses]

    def check_conjunctions(self, dependencies, element, obj, actor, active):
        results = []
        conjs = Search.find_dependencies(dependencies, CONJ)
        cops = Search.find_dependencies(dependencies, COP)

        if len(conjs) > 0:
            action = element if isinstance(element, Action) else None
            for conj in conjs:
                x_comp_hit = True if action and action.f_xcomp and conj['governorGloss'] in action.f_xcomp.f_baseForm else False
                if (conj['governorGloss'] == element.f_name
                    and len(Search.filter_by_gov(cops, conj['governor'])) == 0) \
                        or x_comp_hit:
                    dep_index = conj['dependent']
                    if obj:
                        if actor:
                            new_ele = Builder.create_actor(
                                self.f_stanford_sentence,
                                self.f_full_sentence, dep_index,
                                dependencies)
                        else:
                            new_ele = Builder.create_object(
                                self.f_stanford_sentence,
                                self.f_full_sentence, dep_index,
                                dependencies)
                            self.check_np_sub_sentences(dep_index, dependencies, new_ele)
                    else:
                        if x_comp_hit:
                            new_ele = copy(action)
                            new_ele.f_xcomp = Builder.create_action(
                                self.f_stanford_sentence, self.f_full_sentence,
                                dep_index, dependencies, True)
                        else:
                            new_ele = Builder.create_action(
                                self.f_stanford_sentence, self.f_full_sentence,
                                dep_index, dependencies, active)

                    if conj['dependent'] != conj['governor']:
                        results.append(new_ele)
                        self.build_link(element, conj, new_ele)

        return results

    def find_sub_sentences(self, sentence):

        result = Search.find_children(sentence, self.f_sentenceTags)

        for child in sentence:
            if child.label() in ("PP", "ADVP"):
                result.extend(Search.find_children(child,
                                                   self.f_sentenceTags))
                for grandchild in child:
                    result.extend(Search.find_children(grandchild,
                                                       self.f_sentenceTags))

        return result

    def determine_sub_sentence_count(self, sentence):

        result = Search.count_children(sentence, self.f_sentenceTags)

        if result == 1 and sentence[0].label() == WHNP:
            result -= 1

        for child in sentence:
            if child.label() in (PP, ADVP):
                result += Search.count_children(child,
                                                self.f_sentenceTags)
                for grandchild in child:
                    if grandchild.label() == NP:
                        result += Search.count_children(grandchild,
                                                        self.f_sentenceTags)

        return result

    def check_sub_sentences(self, head, dependencies, obj, is_np):

        if head.label() == SBAR:
            leaves = head.leaves()
            start_index = Search.find_sentence_index(self.f_full_sentence, head)
            end_index = start_index + len(leaves)
            ccomps = Search.find_dependencies(dependencies, CCOMP)

            for ccomp in ccomps:
                if start_index < ccomp['dependent'] < end_index:
                    complms = Search.find_dependencies(dependencies, COMPLM)
                    for complm in complms:
                        if complm['governor'] == ccomp['dependent'] and complm['dependentGloss'] == THAT:
                            return

            action = obj if isinstance(obj, Action) else None
            if not action or not action.f_xcomp or start_index > action.f_xcomp.f_word_index or end_index < action.f_xcomp.f_word_index:
                self.analyze_recursive(head, self.filter_dependencies(head, dependencies))
                return
        else:
            if head.label() in (PP, VP, NP, S):
                for child in head:
                    if not isinstance(child, str):
                        self.check_sub_sentences(child, dependencies, obj, is_np)

    @staticmethod
    def remove_examples(verbs):
        examples = []
        for action in verbs:
            for spec in action.f_specifiers:
                if spec.f_name in f_exampleIndicators:
                    examples.append(action)

        return [verb for verb in verbs if verb not in examples]

    def build_link(self, element, dep, new_ele):
        conjunction = None
        conj_type = None
        conj_spec = dep['spec']

        if conj_spec == OR:
            conj_type = XOR
        elif conj_spec == AND:
            conj_type = AND
        elif conj_spec == ANDOR:
            conj_type = OR
        elif conj_spec != BUT:
            self.logger.error("Undefined conjunction relation {}".format(conj_type))

        if conj_type:
            conjunction = ConjunctionElement(element, new_ele, conj_type)

        if conjunction:
            self.f_analyzed_sentence.f_conjs.append(conjunction)

    def check_global_conjunctions(self):
        conj = Search.find_dependencies(self.f_dependencies, CONJ)

        for dep in conj:
            action_from = self.get_action_containing(dep['governor'])
            action_to = self.get_action_containing(dep['dependent'])
            if action_from and action_to:
                self.build_link(action_from, dep, action_to)

    def get_action_containing(self, node_index):
        for action in self.f_analyzed_sentence.f_actions:
            if action.f_word_index == node_index or \
                    (action.f_xcomp and action.f_xcomp.f_word_index == node_index) or \
                    (action.f_copIndex == node_index) or \
                    (action.f_object and action.f_object.f_word_index == node_index):
                return action

    def check_np_sub_sentences(self, dep_index, dependencies, obj):
        if not self.f_ignore_np_subsentences:
            dep_in_tree = Search.find_dep_in_tree(self.f_full_sentence, dep_index)
            head = Search.get_full_phrase_tree(dep_in_tree, NP)
            self.check_sub_sentences(head, dependencies, obj, True)
