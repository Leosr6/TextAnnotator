from copy import deepcopy
from data.SentenceElements import *
from core.Base import Base
from core.WordNetWrapper import WordNetWrapper
from utils import Search, Processing
from utils.Constants import *


class ElementsBuilder(Base):

    def create_actor(self, origin, full_sentence, node_index, dependencies):
        actor = None
        node = Search.find_dep_in_tree(full_sentence, node_index - 1)
        full_noun = self.get_full_noun(node, node_index, dependencies)
        # TODO: implement WordNetWrapper
        if not WordNetWrapper.person_or_system(full_noun, node.label().lower()):
            if node.parent().label() == CD or WordNetWrapper.group_action(node.label()):
                preps = Search.find_dependencies(dependencies, PREP)
                for spec in preps:
                    # TODO: spec['dep'].getSpecific
                    if spec['dep'] in f_realActorPPIndicators:
                        dep_in_tree = Search.find_dep_in_tree(full_sentence, spec['governor'] - 1)
                        if dep_in_tree == node:
                            dep_index = spec['dependent']
                            dep_in_tree = Search.find_dep_in_tree(full_sentence, dep_index - 1)
                            full_noun = self.get_full_noun(dep_in_tree, dep_index, dependencies)
                            if WordNetWrapper.person_or_system(full_noun, spec['dependentGloss']):
                                actor = self.create_internal_actor(origin, full_sentence, dep_in_tree, dep_index, dependencies)
                                break
            if not actor:
                actor = self.create_internal_actor(origin, full_sentence, node, node_index, dependencies)
                actor.f_unreal = True
        else:
            actor = self.create_internal_actor(origin, full_sentence, node, node_index, dependencies)

        self.logger.debug("Identified actor {}".format(actor))
        return actor

    def create_internal_actor(self, origin, full_sentence, node, node_index, dependencies):
        actor = Actor(origin, node_index, node.label().lower())
        self.determine_noun_specifiers(origin, full_sentence, node, node_index, dependencies, actor)
        full_noun = self.get_full_noun(node, node_index, dependencies)
        if WordNetWrapper.is_meta_actor(full_noun, node.label()):
            actor.f_metaActor = True

        return actor

    def create_action(self, origin, full_sentence, node_index, dependencies, active):
        node = Search.find_dep_in_tree(dependencies, node_index - 1)
        action = Action(origin, node_index, node.label())

        aux = self.get_auxiliars(node_index, dependencies)
        if len(aux) > 0:
            action.f_aux = aux

        mod_index = self.get_modifiers(node_index, dependencies)
        if mod_index:
            mod = Search.find_dep_in_tree(full_sentence, mod_index - 1)
            action.f_mod = mod
            action.f_modPos = mod_index

        action.f_negated = self.is_negated(node, dependencies)

        cop_index = self.get_cop(node_index, dependencies)
        if cop_index:
            cop = Search.find_dep_in_tree(full_sentence, cop_index - 1)
            action.f_cop = cop
            action.f_copIndex = cop_index

        prt = self.get_prt(node_index, dependencies)
        if prt:
            action.f_prt = prt

        iobj_index = self.get_iobj(node_index, dependencies)
        if iobj_index:
            iobj = Search.find_dep_in_tree(full_sentence, iobj_index - 1)
            spec = Specifier(origin, iobj_index, " ".join(iobj.leaves()))
            spec.f_type = IOBJ
            action.f_specifiers.append(spec)

        if not active:
            self.check_dobj(node_index, dependencies, action, origin, full_sentence)

        to_check = Search.find_dependencies(dependencies, (XCOMP, DEP))

        for dep in to_check:
            if dep['governor'] == node_index:
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['governor'] - 1)
                if dep['dep'] == DEP:
                    if dep_in_tree.parent().label()[0] != "V" or dep['dependent'] < dep['governor']:
                        continue

                xcomp = self.create_action(origin, full_sentence, dep['dependent'], dependencies, True)
                action.f_xcomp = xcomp
                break

        vp_head = Search.get_full_phrase_tree(node, VP)
        self.extract_SBAR_spec(origin, full_sentence, action, vp_head)
        self.extract_PP_spec(origin, full_sentence, action, node_index, dependencies)
        self.extract_RCMOD_spec(origin, full_sentence, action, node_index, dependencies)

        self.logger.debug("Identified action {}".format(action))
        return action

    def create_object(self, origin, full_sentence, node_index, dependencies):
        node = Search.find_dep_in_tree(full_sentence, node_index - 1)
        full_noun = self.get_full_noun(node, node_index, dependencies)

        if WordNetWrapper.person_or_system(full_noun, node.label().lower()) or Processing.person_pronoun(node.label()):
            result = self.create_internal_actor(origin, full_sentence, node, node_index, dependencies)
        else:
            result = Resource(origin, node_index, node.label().lower())
            self.determine_noun_specifiers(origin, full_sentence, node, node_index, dependencies, result)

        result.f_subjectRole = False
        self.logger.debug("Identified object {}".format(result))
        return result

    def create_action_syntax(self, origin, full_sentence, vphead):
        verb_parts = self.extract_verb_parts(vphead)
        if isinstance(vphead, str):
            index = Search.find_sentence_index(full_sentence, vphead)
        else:
            index = Search.find_sentence_index(full_sentence, vphead.leaves()[0])

        action = Action(origin, index, " ".join(verb_parts))
        self.extract_SBAR_spec(origin, full_sentence, action, vphead)
        self.extract_PP_spec_syntax(origin, full_sentence, action, vphead)

        self.logger.debug("Identified action {}".format(action))
        return action

    @staticmethod
    def get_full_noun(node, node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, (NN, DEP))
        noun = ""
        sufix = ""

        for dep in to_check:
            if dep['governor'] == node_index:
                if dep['dep'] == DEP:
                    if dep['governor'] + 1 != dep['dependent']:
                        continue
                    sufix += " " + dep['dependentGloss']
                else:
                    noun += dep['dependentGloss'] + " "

        noun += node.label() + sufix
        return noun.lower()

    def determine_noun_specifiers(self, origin, full_sentence, node, node_index, dependencies, element):

        # TODO
        self.find_determiner(node_index, dependencies, element)
        self.find_AMOD_specifiers(origin, node_index, dependencies, element)
        self.find_NN_specifiers(origin, node_index, dependencies, element)
        self.find_INFMOD_specifiers(origin, node_index, dependencies, element)
        self.get_PARTMOD_specifiers(origin, full_sentence, node_index, dependencies, element)
        self.get_specifier_from_dependencies(origin, node_index, dependencies, element, NUM)

        phrase_tree = Search.get_full_phrase_tree(node, NP)
        self.extract_SBAR_spec(origin, full_sentence, element, phrase_tree)
        self.extract_PP_spec(origin, full_sentence, element, node_index, dependencies)

        if node.parent().label() in f_relativeResolutionTags or node.label() in f_relativeResolutionWords:
            if len(node.parent().parent()) == 1:
                for spec in element.get_specifiers(PP):
                    if spec.f_headWord == OF:
                        return
                element.f_needsResolve = True

    @staticmethod
    def find_dependants(node_index, dependencies, deps, is_governor):
        to_check = Search.find_dependencies(dependencies, deps)
        dependants = ""

        for dep in to_check:
            if is_governor:
                if dep['governor'] == node_index:
                    dependants += dep['dependentGloss'] + " "
            else:
                if dep['dependent'] == node_index:
                    dependants += dep['governorGloss'] + " "

        return dependants[:-1]

    def get_auxiliars(self, node_index, dependencies):
        return self.find_dependants(node_index, dependencies, (AUX, AUXPASS), True)

    @staticmethod
    def get_modifiers(node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, (ADVMOD, ACOMP))

        for dep in to_check:
            if dep['governor'] == node_index:
                if dep['governor'] < dep['dependent'] and dep['dependentGloss'] not in f_sequenceIndicators:
                    return dep['dependent']

    @staticmethod
    def is_negated(node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, COP)
        index = node_index

        for dep in to_check:
            if dep['dependent'] == node_index:
                index = dep['governor']
                break

        to_check = Search.find_dependencies(dependencies, NEG)

        for dep in to_check:
            if dep['governor'] == index:
                return True

        return False

    @staticmethod
    def get_cop(node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, COP)

        for dep in to_check:
            if dep['dependent'] == node_index:
                return dep['governor']

    def get_prt(self, node_index, dependencies):
        return self.find_dependants(node_index, dependencies, (PRT,), True)

    @staticmethod
    def get_iobj(node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, IOBJ)

        for dep in to_check:
            if dep['dependent'] == node_index:
                return dep['governor']

    def check_dobj(self, node_index, dependencies, action, origin, full_sentence):
        to_check = Search.find_dependencies(dependencies, DOBJ)

        for dep in to_check:
            if dep['governor'] == node_index:
                self.logger.error("Dobj was found in a passive sentence")
                node = Search.find_dep_in_tree(full_sentence, dep['dependent'] - 1)
                spec = Specifier(origin, dep['dependent'], self.get_full_noun(node, dep['dependent'], dependencies))
                spec.f_type = DOBJ
                obj = self.create_object(origin, full_sentence, dep['dependent'], dependencies)
                spec.f_object = obj
                action.f_specifiers.append(spec)

    @staticmethod
    def extract_SBAR_spec(origin, full_sentence, element, vp_head):
        sbar_list = Search.find_in_tree(vp_head, SBAR, [])
        vp_index = Search.find_sentence_index(full_sentence, vp_head.leaves())

        for sbar in sbar_list:
            sbar_index = Search.find_sentence_index(full_sentence, sbar.leaves())

            if sbar_index > vp_index:
                spec = Specifier(origin, sbar_index, " ".join(sbar.leaves()))
                spec.f_type = SBAR
                element.f_specifiers.append(spec)

    def extract_PP_spec(self, origin, full_sentence, element, node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, (PREP, PREPC))
        rc_mod = Search.find_dependencies(dependencies, RCMOD)

        for dep in to_check:
            cop = element.f_cop if isinstance(element, Action) else None
            if (dep['governor'] == node_index or dep['governorGloss'] == cop) and not self.part_rc_mod(full_sentence, rc_mod, dep):
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['dependent'] - 1)
                phrase_tree = Search.get_full_phrase_tree(dep_in_tree, PP)
                # TODO: check print
                phrase = " ".join(phrase_tree.leaves())
                specific = None
                space_index = phrase.index(" ")
                if space_index >= 0:
                    # TODO: conj['dep'].getSpecific
                    if dep['dep']:
                        phrase = phrase[space_index:]
                        # TODO: conj['dep'].getSpecific
                        specific = dep['dep'].replace("_", " ")
                        phrase = specific + phrase
                    spec = Specifier(origin, dep['dependent'], phrase)
                    spec.f_type = PP
                    if NP in dep_in_tree.parent().parent().label():
                        obj = self.create_object(origin, full_sentence, dep['dependent'], dependencies)
                        spec.f_object = obj
                    spec.f_headWord = specific
                    # TODO: FrameNetWrapper.determineSpecifierFrameElement(element, _sp);
                    element.f_specifiers.append(spec)

    def extract_RCMOD_spec(self, origin, full_sentence, element, node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, RCMOD)

        for dep in to_check:
            cop = element.f_cop if isinstance(element, Action) else None
            if dep['dependent'] == node_index or dep['dependentGloss'] == cop:
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['governor'] - 1)
                phrase_tree = Search.get_full_phrase_tree(dep_in_tree, PP)
                if phrase_tree:
                    phrase_tree = self.delete_branches(phrase_tree, (S, SBAR))
                    # TODO: check print
                    phrase = " ".join(phrase_tree.leaves())
                    spec = Specifier(origin, dep['dependent'], phrase)
                    spec.f_type = RCMOD
                    element.f_specifiers.append(spec)

    @staticmethod
    def extract_PP_spec_syntax(origin, full_sentence, element, vphead):
        pp_list = Search.find_in_tree(vphead, PP, (SBAR, S, NP, PRN))

        for pp in pp_list:
            pp_index = Search.find_sentence_index(full_sentence, pp.leaves())
            # TODO: check print
            spec = Specifier(origin, pp_index, " ".join(pp.leaves()))
            spec.f_type = PP
            element.f_specifiers.append(spec)

    def extract_verb_parts(self, node):
        parts = []
        if isinstance(node[0], str):
            parts.append(node)
        else:
            for child in node:
                if child.label() not in (SBAR, NP, ADJP, ADVP, PRN) and node.label() != PP:
                    parts.extend(self.extract_verb_parts(child))

        return parts

    def part_rc_mod(self, full_sentence, rc_mod, dep):
        for rcm in rc_mod:
            if rcm['governor'] == dep['dependent']:
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['dependent'] - 1)
                phrase_tree = Search.get_full_phrase_tree(dep_in_tree, PP)
                phrase_tree = self.delete_branches(phrase_tree, (S, SBAR))
                phrase = " ".join(phrase_tree.leaves()).lower()
                if phrase in f_conditionIndicators:
                    return True

        return False

    @staticmethod
    def find_determiner(node_index, dependencies, element):
        to_check = Search.find_dependencies(dependencies, (POSS, DET))

        for dep in to_check:
            if dep['governor'] == node_index:
                element.f_determiner = dep['governorGloss']
                break

    def find_AMOD_specifiers(self, origin, node_index, dependencies, element):
        self.get_specifier_from_dependencies(origin, node_index, dependencies, element, AMOD)

    def find_NN_specifiers(self, origin, node_index, dependencies, element):
        self.get_specifier_from_dependencies(origin, node_index, dependencies, element, NN)
        to_check = Search.find_dependencies(dependencies, DEP)

        for dep in to_check:
            if dep['governor'] == node_index:
                if dep['governor'] + 1 != dep['dependent']:
                    continue
                spec = Specifier(origin, dep['dependent'], dep['dependentGloss'].lower())
                spec.f_type = NNAFTER
                element.f_specifiers.append(spec)

    @staticmethod
    def find_INFMOD_specifiers(origin, node_index, dependencies, element):
        to_check = Search.find_dependencies(dependencies, INFMOD)
        name = ""

        for dep in to_check:
            if dep['governor'] == node_index:
                to_check = Search.find_dependencies(dependencies, (AUX, COP, NEG))
                for acn in to_check:
                    if acn['governor'] == dep['dependent']:
                        name += acn['dependentGloss'] + " "
                name += dep['dependentGloss']
                spec = Specifier(origin, dep['dependent'], name)
                spec.f_type = INFMOD
                element.f_specifiers.append(spec)
                break

    @staticmethod
    def get_PARTMOD_specifiers(origin, full_sentence, node_index, dependencies, element):
        to_check = Search.find_dependencies(dependencies, PARTMOD)

        for dep in to_check:
            if dep['governor'] == node_index:
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['dependent'])
                phrase = Search.get_full_phrase_tree(dep_in_tree, VP)
                spec = Specifier(origin, dep['dependent'], phrase)
                spec.f_type = PARTMOD
                element.f_specifiers.append(spec)

    @staticmethod
    def get_specifier_from_dependencies(origin, node_index, dependencies, element, dep_type):
        to_check = Search.find_dependencies(dependencies, dep_type)
        index = None
        name = ""

        for dep in to_check:
            if dep['governor'] == node_index:
                name += dep['dependentGloss'] + " "
                conjs = Search.find_dependencies(dependencies, CONJ)
                for conj in conjs:
                    if conj['governor'] == dep['dependent']:
                        # TODO: conj['dep'].getSpecific
                        name += conj['dep'] + " " + dep['dependentGloss'] + " "
                if not index:
                    index = dep['dependent']

        if index:
            name = name[:-1]
            spec = Specifier(origin, index, name)
            spec.f_type = dep_type
            element.f_specifiers.append(spec)

    def delete_branches(self, tree, branches):
        result = deepcopy(tree)
        self.delete_branches_recursive(result, branches)
        return result

    def delete_branches_recursive(self, tree, branches):
        for child in tree:
            if child.label() in branches:
                index = child.treeposition()[1:]
                del(tree[index])
            else:
                self.delete_branches_recursive(child, branches)
