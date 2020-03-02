from time import time
from copy import deepcopy
from core import Base
from data import AnalyzedSentence, SentenceElements
from utils import Search
from utils.Constants import *

class SentenceAnalyzer(Base):

    f_world = None
    f_sentenceNumber = time()
    f_sentenceTags = ["S", "SBAR", "SINV"]
    f_tokens = []
    f_dependencies = []
    f_analyzed_sentence = None
    f_full_sentence = ""

    def __init__(self, world_model):

        self.f_world = world_model

    def analyze_sentence(self, sentence):

        self.f_sentenceNumber += 1
        self.f_full_sentence = sentence.f_tree
        self.f_tokens = sentence.f_tokens
        self.f_dependencies = sentence.f_dependencies
        self.f_analyzed_sentence = AnalyzedSentence(sentence, sentence.f_tree,
                                                    self.f_sentenceNumber)

        dependencies = sentence.f_dependencies
        main_sentence = root[0]

        self.analyze_recursive(main_sentence, dependencies)

        return self.f_analyzed_sentence

    def analyze_recursive(self, main_sentence, dependencies):

        sub_sentence_count = self.determine_sub_sentence_count(main_sentence)

        if sub_sentence_count == 0:
            self.extract_elements(main_sentence, dependencies)
        elif sub_sentence_count == 1:
            sub_sentence = self.find_sub_sentences(main_sentence)[0]
            filtered_dependencies = self.filter_dependencies(sub_sentence,
                                                             dependencies)
            self.analyze_recursive(sub_sentence, filtered_dependencies)
        else:
            sub_sentences = self.find_sub_sentences(main_sentence)
            for sub_sentence in sub_sentences:
                filtered_dependencies = self.filter_dependencies(sub_sentence,
                                                                 dependencies)
                self.analyze_recursive(sub_sentence, filtered_dependencies)

    def extract_elements(self, sentence, dependencies):

        active = self.is_active_sentence(sentence, dependencies)
        actors = self.determine_subjects(sentence, dependencies, active)
        verbs = self.determine_verbs(sentence, dependencies, active)

        actions = []
        all_objects = []

        # Creating actions from verbs
        for verb in verbs:
            objects = self.determine_object(sentence, verb, dependencies, active)
            # TO-DO: filterVerb(verb, _actors, _objects);
            all_objects.extend(objects)

            if len(objects) > 0:
                # One verb can generate multiple actions
                for el in objects:
                    new_action = deepcopy(verb)
                    new_action["object"] = el
                    actions.append(new_action)
            else:
                actions.append(verb)

        final_actions = []

        # Combining actors with actions
        if len(actors) > 0:
            for actor in actors:
                for action in actions:
                    new_action = deepcopy(action)
                    new_action["actor"] = actor
                    final_actions.append(new_action)
        else:
            final_actions = actions

        # Add everything to the world model

        for actor in actors:
            self.f_world.add_actor(actor)

        for el in all_objects:
            if isinstance(el, SentenceElements.Actor):
                self.f_world.add_actor(el)
            else:
                self.f_world.add_resource(el)

        for action in actions:
            self.f_analyzed_sentence.add_action(action)
            actor = action.get("actor")
            el = action.get("object")
            if actor:
                self.f_world.add_actor(actor)
            if el:
                if isinstance(el, SentenceElements.Actor):
                    self.f_world.add_actor(el)
                else:
                    self.f_world.add_resource(el)


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

        main_actor = None

        # Find main actor

        subj = Search.find_dependencies(dependencies, NSUBJ) if active else \
               Search.find_dependencies(dependencies, AGENT)

        subj = self.exclude_relative_clauses(sentence, subj)
        if len(subj) == 0:
            self.logger.debug("Sentence contains no subject!")
        elif len(subj) == 1:
            main_actor = subj[0]['dependentGloss']
        else:
            self.logger.info("Sentence has more then one subject")
            self.logger.debug(subj)

        # Find all actors

        if main_actor:
            # TO-DO: fix
            actor = SentenceElements.Actor(sentence, self.f_fullSentence, main_actor, dependencies)
            actor.subject = True
            actor.passive = not active
            actors.append(actor)
            # TO-DO: fix
            for new_actor in self.check_conjunctions(dependencies, actor, True, True, active):
                new_actor.subject = True
                new_actor.passive = not active
                actors.append(new_actor)

        return actors

    def determine_verbs(self, sentence, dependencies, active):
        actions = []

        main_predicate = None

        # Determine main predicate

        if active:
            nsubj = Search.find_dependencies(dependencies, NSUBJ)
            nsubj = self.exclude_relative_clauses(sentence, nsubj)
            if len(nsubj) == 0:
                dobj = Search.find_dependencies(dependencies, DOBJ)
                dobj = self.exclude_relative_clauses(sentence, dobj)
                if len(dobj) >= 1:
                    main_predicate = dobj[0]['governorGloss']
            elif len(nsubj) == 1:
                main_predicate = nsubj[0]['governorGloss']
                cop = Search.find_dependencies(dependencies, COP)
                cop = self.exclude_relative_clauses(sentence, cop)
                for dep in cop:
                    if dep['governorGloss'] == main_predicate:
                        main_predicate = dep['dependentGloss']
                        break
            else:
                self.logger.info("Sentence has more than one active predicate")
                self.logger.debug(nsubj)

        else:
            nsubjpass = Search.find_dependencies(dependencies, NSUBJPASS)
            nsubjpass = self.exclude_relative_clauses(sentence, nsubjpass)
            if len(nsubjpass) == 1:
                main_predicate = nsubjpass[0]['governorGloss']
            elif len(nsubjpass) > 1:
                self.logger.info("Sentence has more than one passive predicate")
                self.logger.debug(nsubjpass)

        # Find all actions

        # TO-DO: implement
        if main_predicate:
            vp_head = Search.get_full_phrase_tree(main_predicate, VP)
        else:
            verbs = Search.find_in_tree(sentence, VP, (SBAR, S))
            vp_head = verbs[0] if len(verbs) == 1 else None

        if vp_head:
            # TO-DO: implement
            vp_head = Search.get_full_phrase_tree(main_predicate, VP)
            action = SentenceElements.Action(sentence, self.full_sentence, main_predicate, dependencies, active)
            self.check_sub_sentences(vp_head, dependencies, action, False)
            actions.append(action)
        elif not verbs or len(verbs) == 0:
            self.logger.info("Sentence contains no action")
        else:
            self.logger.info("Sentence has more than one verb phrase")

        if len(actions) > 0:
            # TO-DO: fix
            for new_action in self.check_conjunctions(dependencies, actions[0], False,
                                                    False, active):
                actions.append(new_action)

        return actions

    def exclude_relative_clauses(self, sentence, dependencies):

        relative_clauses = []

        for dep in dependencies:
            if dep['dep'] != RELCL:
                sentence_index = Search.find_sentence_index(self.f_full_sentence,
                                                           sentence)
                dep_index = dep['dependent'] - 1
                dep_in_tree = Search.find_dep_in_tree(self.f_full_sentence,
                                                      dep_index)

                while dep_in_tree.label() != ROOT:

                    if sentence.label() == dep_in_tree.label():
                        if sentence_index >= dep_index:
                            break

                    if dep_in_tree.label() in (SBAR, S, PRN) and dep_in_tree.parent().label() != SBAR:
                        relative_clauses.append(dep)
                        break

        return [dep for dep in dependencies if dep not in relative_clauses]

    def check_conjunctions(self, dependencies, element, object, actor, active):
        results = []
        conjs = Search.find_dependencies(dependencies, CONJ)
        cops = Search.find_dependencies(dependencies, COP)

        if len(conjs) > 0:
            action = element if isinstance(element, SentenceElements.Action)
            for conj in conjs:
                # TO-DO: boolean _xcompHit = (a != null && a.getXcomp() != null && a.getXcomp().getVerb().contains(td.gov().value()));
                _xcompHit = True
                if (conj['governorGloss'] == element.f_name
                        and len(Search.filter_by_gov(conj, cops)) == 0) \
                    or _xcompHit:
                    dep_index = dep['dependent'] - 1
                    dep_in_tree = Search.find_dep_in_tree(self.f_full_sentence,
                                                          dep_index)
                    if object:
                        if actor:
                            new_ele = SentenceElements.Actor()
                        else:
                            new_ele = SentenceElements.Object()
                    else:
                        if _xcompHit:
                            new_ele = deepcopy(action)
                            # TO-DO: _newEle.setXcomp()
                        else:
                            new_ele = SentenceElements.Action()

                    if conj['dependent'] != conj['governor']:
                        results.append(new_ele)
                        # TO-DO: buildLink(current, td, _newEle);

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

        if result == 1 and sentence.label() == "WHNP":
            result -= 1

        for child in sentence:
            if child.label() in ("PP", "ADVP"):
                result += Search.count_children(child,
                                                self.f_sentenceTags)
                for grandchild in child:
                    if grandchild.label() == "NP":
                        result += Search.count_children(grandchild,
                                                        self.f_sentenceTags)

        return result


