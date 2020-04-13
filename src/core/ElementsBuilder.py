from copy import deepcopy
from data.SentenceElements import *
from core.Base import Base
from core.WordNetWrapper import WordNetWrapper
from utils import Search, Processing
from utils.Constants import *


class ElementsBuilder(Base):

    @classmethod
    def create_actor(cls, origin, full_sentence, node_index, dependencies):
        actor = None
        node = Search.find_dep_in_tree(full_sentence, node_index)
        full_noun = cls.get_full_noun(node, node_index, dependencies)
        if not WordNetWrapper.person_or_system(full_noun, node[0]):
            if node.label() == CD or WordNetWrapper.can_be_group_action(node[0]):
                preps = Search.find_dependencies(dependencies, PREP)
                for spec in preps:
                    if spec['spec'] in f_realActorPPIndicators and spec['governor'] == node_index:
                        dep_index = spec['dependent']
                        dep_in_tree = Search.find_dep_in_tree(full_sentence, dep_index)
                        full_noun = cls.get_full_noun(dep_in_tree, dep_index, dependencies)
                        if WordNetWrapper.person_or_system(full_noun, spec['dependentGloss']):
                            actor = cls.create_internal_actor(origin, full_sentence, dep_in_tree, dep_index, dependencies)
                            break
            if not actor:
                actor = cls.create_internal_actor(origin, full_sentence, node, node_index, dependencies)
                actor.f_unreal = True
        else:
            actor = cls.create_internal_actor(origin, full_sentence, node, node_index, dependencies)

        cls.logger.debug("Identified actor {}".format(actor))
        return actor

    @classmethod
    def create_internal_actor(cls, origin, full_sentence, node, node_index, dependencies):
        actor = Actor(origin, node_index, node[0])
        cls.determine_noun_specifiers(origin, full_sentence, node, node_index, dependencies, actor)
        full_noun = cls.get_full_noun(node, node_index, dependencies)
        if WordNetWrapper.is_meta_actor(full_noun, node[0]):
            actor.f_metaActor = True

        return actor

    @classmethod
    def create_action(cls, origin, full_sentence, node_index, dependencies, active):
        node = Search.find_dep_in_tree(full_sentence, node_index)
        action = Action(origin, node_index, node[0])

        aux = cls.get_auxiliars(node_index, dependencies)
        if len(aux) > 0:
            action.f_aux = aux

        mod_index = cls.get_modifiers(node_index, dependencies)
        if mod_index:
            mod = Search.find_dep_in_tree(full_sentence, mod_index)
            action.f_mod = mod[0]
            action.f_modPos = mod_index

        action.f_negated = cls.is_negated(node, dependencies)

        cop_index = cls.get_cop(node_index, dependencies)
        if cop_index:
            cop = Search.find_dep_in_tree(full_sentence, cop_index)
            action.f_cop = cop[0]
            action.f_copIndex = cop_index

        prt = cls.get_prt(node_index, dependencies)
        if prt:
            action.f_prt = prt

        iobj_index = cls.get_iobj(node_index, dependencies)
        if iobj_index:
            iobj = Search.find_dep_in_tree(full_sentence, iobj_index)
            spec = Specifier(origin, iobj_index, " ".join(iobj.leaves()))
            spec.f_type = IOBJ
            action.f_specifiers.append(spec)

        if not active:
            cls.check_dobj(node_index, dependencies, action, origin, full_sentence)

        to_check = Search.find_dependencies(dependencies, (XCOMP, DEP))

        for dep in to_check:
            if dep['governor'] == node_index:
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['dependent'])
                if dep['dep'] == DEP:
                    if dep_in_tree.label()[0] != "V" or dep['dependent'] < dep['governor']:
                        continue

                xcomp = cls.create_action(origin, full_sentence, dep['dependent'], dependencies, True)
                action.f_xcomp = xcomp
                break

        vp_head = Search.get_full_phrase_tree(node, VP)
        cls.extract_SBAR_spec(origin, full_sentence, action, vp_head)
        cls.extract_PP_spec(origin, full_sentence, action, node_index, dependencies)
        cls.extract_RCMOD_spec(origin, full_sentence, action, node_index, dependencies)

        cls.logger.debug("Identified action {}".format(action))
        return action

    @classmethod
    def create_object(cls, origin, full_sentence, node_index, dependencies):
        node = Search.find_dep_in_tree(full_sentence, node_index)
        full_noun = cls.get_full_noun(node, node_index, dependencies)

        if WordNetWrapper.person_or_system(full_noun, node[0]) or Processing.can_be_person_pronoun(node[0]):
            result = cls.create_internal_actor(origin, full_sentence, node, node_index, dependencies)
        else:
            result = Resource(origin, node_index, node[0])
            cls.determine_noun_specifiers(origin, full_sentence, node, node_index, dependencies, result)

        result.f_subjectRole = False
        cls.logger.debug("Identified object {}".format(result))
        return result

    @classmethod
    def create_action_syntax(cls, origin, full_sentence, vphead):
        verb_parts = cls.extract_verb_parts(vphead)
        # TODO: check if necessary
        # if isinstance(vphead, str):
        #     index = Search.find_sentence_index(full_sentence, vphead)
        # else:
        index = Search.find_sentence_index(full_sentence, vphead)

        action = Action(origin, index, " ".join(verb_parts))
        cls.extract_SBAR_spec(origin, full_sentence, action, vphead)
        cls.extract_PP_spec_syntax(origin, full_sentence, action, vphead)

        cls.logger.debug("Identified action {}".format(action))
        return action

    @classmethod
    def get_full_noun(cls, node, node_index, dependencies):
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

        noun += node[0] + sufix
        return noun

    @classmethod
    def determine_noun_specifiers(cls, origin, full_sentence, node, node_index, dependencies, element):

        cls.find_determiner(node_index, dependencies, element)
        cls.find_AMOD_specifiers(origin, node_index, dependencies, element)
        cls.find_NN_specifiers(origin, node_index, dependencies, element)
        cls.find_INFMOD_specifiers(origin, node_index, dependencies, element)
        cls.get_PARTMOD_specifiers(origin, full_sentence, node_index, dependencies, element)
        cls.get_specifier_from_dependencies(origin, node_index, dependencies, element, NUM)

        phrase_tree = Search.get_full_phrase_tree(node, NP)
        cls.extract_SBAR_spec(origin, full_sentence, element, phrase_tree)
        cls.extract_PP_spec(origin, full_sentence, element, node_index, dependencies)

        if node.label() in f_relativeResolutionTags or node[0] in f_relativeResolutionWords:
            if len(node.parent()) == 1:
                for spec in element.get_specifiers(PP):
                    if spec.f_headWord == OF:
                        return
                element.f_needsResolve = True

    @classmethod
    def find_dependants(cls, node_index, dependencies, deps, is_governor):
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

    @classmethod
    def get_auxiliars(cls, node_index, dependencies):
        return cls.find_dependants(node_index, dependencies, (AUX, AUXPASS), True)

    @classmethod
    def get_modifiers(cls, node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, (ADVMOD, ACOMP))

        for dep in to_check:
            if dep['governor'] == node_index:
                if dep['governor'] < dep['dependent'] and dep['dependentGloss'] not in f_sequenceIndicators:
                    return dep['dependent']

    @classmethod
    def is_negated(cls, node_index, dependencies):
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

    @classmethod
    def get_cop(cls, node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, COP)

        for dep in to_check:
            if dep['dependent'] == node_index:
                return dep['governor']

    @classmethod
    def get_prt(cls, node_index, dependencies):
        return cls.find_dependants(node_index, dependencies, (PRT,), True)

    @classmethod
    def get_iobj(cls, node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, IOBJ)

        for dep in to_check:
            if dep['dependent'] == node_index:
                return dep['governor']

    @classmethod
    def check_dobj(cls, node_index, dependencies, action, origin, full_sentence):
        to_check = Search.find_dependencies(dependencies, DOBJ)

        for dep in to_check:
            if dep['governor'] == node_index:
                cls.logger.error("Dobj was found in a passive sentence")
                node = Search.find_dep_in_tree(full_sentence, dep['dependent'])
                spec = Specifier(origin, dep['dependent'], cls.get_full_noun(node, dep['dependent'], dependencies))
                spec.f_type = DOBJ
                obj = cls.create_object(origin, full_sentence, dep['dependent'], dependencies)
                spec.f_object = obj
                action.f_specifiers.append(spec)

    @classmethod
    def extract_SBAR_spec(cls, origin, full_sentence, element, vp_head):
        sbar_list = Search.find_in_tree(vp_head, SBAR, [])
        vp_index = Search.find_sentence_index(full_sentence, vp_head)

        for sbar in sbar_list:
            sbar_index = Search.find_sentence_index(full_sentence, sbar)

            if sbar_index > vp_index:
                spec = Specifier(origin, sbar_index, " ".join(sbar.leaves()))
                spec.f_type = SBAR
                element.f_specifiers.append(spec)

    @classmethod
    def extract_PP_spec(cls, origin, full_sentence, element, node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, (PREP, PREPC))
        rc_mod = Search.find_dependencies(dependencies, RCMOD)

        for dep in to_check:
            cop = element.f_cop if isinstance(element, Action) else None
            if (dep['governor'] == node_index or dep['governorGloss'] == cop) and not cls.part_rc_mod(full_sentence, rc_mod, dep):
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['dependent'])
                phrase_tree = Search.get_full_phrase_tree(dep_in_tree, PP)
                # TODO: check print
                phrase = " ".join(phrase_tree.leaves())
                space_index = phrase.index(" ")
                if space_index >= 0:
                    specific = dep['spec']
                    if specific:
                        phrase = phrase[space_index:]
                        phrase = specific + phrase
                    spec = Specifier(origin, dep['dependent'], phrase)
                    spec.f_type = PP
                    if dep_in_tree.parent().label().startswith(NP):
                        obj = cls.create_object(origin, full_sentence, dep['dependent'], dependencies)
                        spec.f_object = obj
                    spec.f_headWord = specific
                    # TODO: FrameNetWrapper.determineSpecifierFrameElement(element, _sp);
                    element.f_specifiers.append(spec)

    @classmethod
    def extract_RCMOD_spec(cls, origin, full_sentence, element, node_index, dependencies):
        to_check = Search.find_dependencies(dependencies, RCMOD)

        for dep in to_check:
            cop = element.f_cop if isinstance(element, Action) else None
            if dep['dependent'] == node_index or dep['dependentGloss'] == cop:
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['governor'])
                phrase_tree = Search.get_full_phrase_tree(dep_in_tree, PP)
                if phrase_tree:
                    phrase_tree = cls.delete_branches(phrase_tree, (S, SBAR))
                    # TODO: check print
                    phrase = " ".join(phrase_tree.leaves())
                    spec = Specifier(origin, dep['dependent'], phrase)
                    spec.f_type = RCMOD
                    element.f_specifiers.append(spec)

    @classmethod
    def extract_PP_spec_syntax(cls, origin, full_sentence, element, vphead):
        pp_list = Search.find_in_tree(vphead, PP, (SBAR, S, NP, PRN))

        for pp in pp_list:
            pp_index = Search.find_sentence_index(full_sentence, pp)
            # TODO: check print
            spec = Specifier(origin, pp_index, " ".join(pp.leaves()))
            spec.f_type = PP
            element.f_specifiers.append(spec)

    @classmethod
    def extract_verb_parts(cls, node):
        parts = []
        if isinstance(node[0], str):
            parts.append(node[0])
        else:
            for child in node:
                if child.label() not in (SBAR, NP, ADJP, ADVP, PRN, S) and node.label() != PP:
                    parts.extend(cls.extract_verb_parts(child))

        return parts

    @classmethod
    def part_rc_mod(cls, full_sentence, rc_mod, dep):
        for rcm in rc_mod:
            if rcm['governor'] == dep['dependent']:
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['dependent'])
                phrase_tree = Search.get_full_phrase_tree(dep_in_tree, PP)
                phrase_tree = cls.delete_branches(phrase_tree, (S, SBAR))
                phrase = " ".join(phrase_tree.leaves())
                if phrase in f_conditionIndicators:
                    return True

        return False

    @classmethod
    def find_determiner(cls, node_index, dependencies, element):
        to_check = Search.find_dependencies(dependencies, (POSS, DET))

        for dep in to_check:
            if dep['governor'] == node_index:
                element.f_determiner = dep['dependentGloss']
                break

    @classmethod
    def find_AMOD_specifiers(cls, origin, node_index, dependencies, element):
        cls.get_specifier_from_dependencies(origin, node_index, dependencies, element, AMOD)

    @classmethod
    def find_NN_specifiers(cls, origin, node_index, dependencies, element):
        cls.get_specifier_from_dependencies(origin, node_index, dependencies, element, NN)
        to_check = Search.find_dependencies(dependencies, DEP)

        for dep in to_check:
            if dep['governor'] == node_index:
                if dep['governor'] + 1 != dep['dependent']:
                    continue
                spec = Specifier(origin, dep['dependent'], dep['dependentGloss'])
                spec.f_type = NNAFTER
                element.f_specifiers.append(spec)

    @classmethod
    def find_INFMOD_specifiers(cls, origin, node_index, dependencies, element):
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

    @classmethod
    def get_PARTMOD_specifiers(cls, origin, full_sentence, node_index, dependencies, element):
        to_check = Search.find_dependencies(dependencies, PARTMOD)

        for dep in to_check:
            if dep['governor'] == node_index:
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['dependent'])
                phrase_tree = Search.get_full_phrase_tree(dep_in_tree, VP)
                phrase = phrase_tree.leaves() if phrase_tree else []
                spec = Specifier(origin, dep['dependent'], " ".join(phrase))
                spec.f_type = PARTMOD
                element.f_specifiers.append(spec)

    @classmethod
    def get_specifier_from_dependencies(cls, origin, node_index, dependencies, element, dep_type):
        to_check = Search.find_dependencies(dependencies, dep_type)
        index = None
        name = ""

        for dep in to_check:
            if dep['governor'] == node_index:
                name += dep['dependentGloss'] + " "
                conjs = Search.find_dependencies(dependencies, CONJ)
                for conj in conjs:
                    if conj['governor'] == dep['dependent']:
                        name += conj['spec'] + " " + dep['dependentGloss'] + " "
                if not index:
                    index = dep['dependent']

        if index:
            name = name[:-1]
            spec = Specifier(origin, index, name)
            spec.f_type = dep_type
            element.f_specifiers.append(spec)

    @classmethod
    def delete_branches(cls, tree, branches):
        result = deepcopy(tree)
        cls.delete_branches_recursive(result, branches)
        return result

    @classmethod
    def delete_branches_recursive(cls, tree, branches):
        for child in tree:
            if not isinstance(child, str):
                if child.label() in branches:
                    index = child.treeposition()[1:]
                    del(tree[index])
                else:
                    cls.delete_branches_recursive(child, branches)
