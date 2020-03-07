from data.SentenceElements import *
from core.Base import Base
from core.WordNetWrapper import WordNetWrapper
from utils import Search, Processing
from utils.Constants import *


class ElementsBuilder(Base):

    def create_actor(self, origin, full_sentence, node_index, dependencies):
        actor = None
        node = Search.find_dep_in_tree(full_sentence, node_index - 1)
        # TODO
        full_noun = self.get_full_noun(node, dependencies)
        if not WordNetWrapper.person_or_system(full_noun, node.label().lower()):
            if node.parent().label() == CD or WordNetWrapper.group_action(node.label()):
                preps = Search.find_dependencies(dependencies, PREP)
                for spec in preps:
                    # TODO : spec['dep'].getSpecific
                    if spec['dep'] in f_realActorPPIndicators:
                        dep_in_tree = Search.find_dep_in_tree(full_sentence, spec['governor'] - 1)
                        if dep_in_tree == node:
                            dep_index = spec['dependent']
                            dep_in_tree = Search.find_dep_in_tree(full_sentence, dep_index - 1)
                            full_noun = self.get_full_noun(dep_in_tree, dependencies)
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
        # TODO:
        self.determine_noun_specifiers(origin, full_sentence, node, dependencies, actor)
        full_noun = self.get_full_noun(node, dependencies)
        if WordNetWrapper.is_meta_actor(full_noun, node.label()):
            actor.f_metaActor = True

        return actor

    def create_action(self, origin, full_sentence, node_index, dependencies, active):
        node = Search.find_dep_in_tree(dependencies, node_index - 1)
        action = Action(origin, node_index, node.label())

        # TODO:
        aux = self.get_auxiliars(node, dependencies)
        if len(aux) > 0:
            action.f_aux = aux

        # TODO:
        mod_index = self.get_modifiers(node, dependencies)
        if mod_index:
            mod = Search.find_dep_in_tree(full_sentence, mod_index - 1)
            action.f_mod = mod
            action.f_modPos = mod_index

        # TODO:
        action.f_negated = self.is_negated(node, dependencies)

        # TODO:
        cop_index = self.get_cop(node, dependencies)
        if cop_index:
            cop = Search.find_dep_in_tree(full_sentence, cop_index - 1)
            action.f_cop = cop
            action.f_copIndex = cop_index

        # TODO:
        prt = self.get_prt(node, dependencies)
        if prt:
            action.f_prt = prt

        iobj_index = self.get_iobj(node, dependencies)
        if iobj_index:
            iobj = Search.find_dep_in_tree(full_sentence, iobj_index - 1)
            spec = Specifier(origin, iobj_index, " ".join(iobj.leaves()))
            spec.f_type = IOBJ
            action.f_specifiers.append(spec)

        if not active:
            # TODO:
            action = self.check_dobj(node, dependencies, action, origin, full_sentence)

        to_check = Search.find_dependencies(dependencies, (XCOMP, DEP))

        for dep in to_check:
            if dep['governor'] == node_index:
                dep_in_tree = Search.find_dep_in_tree(full_sentence, dep['governor'] - 1)
                if dep['dep'] == DEP:
                    if dep_in_tree.parent().label()[0] != "V" or dep['dependent'] < dep['governor']:
                        continue

                xcomp = self.create_action(origin, full_sentence, dep['dependent'], True)
                action.f_xcomp = xcomp
                break

        vp_head = Search.get_full_phrase_tree(node, VP)
        # TODO:
        action = self.extract_SBAR_spec(origin, full_sentence, action, vp_head, node)
        action = self.extract_PP_spec(origin, full_sentence, action, node, dependencies)
        action = self.extract_RCMOD_spec(origin, action, node, dependencies)

        self.logger.debug("Identified action {}".format(action))
        return action

    def create_object(self, origin, full_sentence, node_index, dependencies):
        node = Search.find_dep_in_tree(full_sentence, node_index - 1)
        full_noun = self.get_full_noun(node, dependencies)

        if WordNetWrapper.person_or_system(full_noun, node.label().lower()) or Processing.person_pronoun(node.label()):
            result = self.create_internal_actor(origin, full_sentence, node, node_index, dependencies)
        else:
            result = Resource(origin, node_index, node.label().lower())
            result = self.determine_noun_specifiers(origin, full_sentence, node, dependencies, result)

        result.f_subjectRole = False
        self.logger.debug("Identified object {}".format(result))
        return result

    def create_action_syntax(self, origin, full_sentence, vphead, active):
        # TODO:
        verb_parts = self.extract_verb_parts(vphead, active)
        if isinstance(vphead, str):
            index = Search.find_sentence_index(full_sentence, vphead)
        else:
            index = Search.find_sentence_index(full_sentence, vphead.leaves()[0])

        action = Action(origin, index, " ".join(verb_parts.leaves()))
        # TODO:
        action = self.extract_SBAR_spec(origin, full_sentence, action, vphead, None)
        action = self.extract_PP_spec_syntax(origin, full_sentence, action, vphead)

        self.logger.debug("Identified action {}".format(action))
        return action

    def get_full_noun(self, node, dependencies):
        pass

    def determine_noun_specifiers(self, origin, full_sentence, node, dependencies, element):
        pass

    def get_auxiliars(self, node, dependencies):
        pass

    def get_modifiers(self, node, dependencies):
        pass

    def is_negated(self, node, dependencies):
        pass

    def get_cop(self, node, dependencies):
        pass

    def get_prt(self, node, dependencies):
        pass

    def get_iobj(self, node, dependencies):
        pass

    def check_dobj(self, node, dependencies, action, origin, full_sentence):
        pass

    def extract_SBAR_spec(self, origin, full_sentence, action, vp_head, node):
        pass

    def extract_PP_spec(self, origin, full_sentence, action, node,
                        dependencies):
        pass

    def extract_RCMOD_spec(self, origin, action, node, dependencies):
        pass

    def extract_PP_spec_syntax(self, origin, full_sentence, action, vphead):
        pass

    def extract_verb_parts(self, vphead, active):
        pass
