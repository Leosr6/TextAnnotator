import nltk
from nltk.corpus import wordnet as wn
from nltk.metrics.distance import edit_distance
from core.Base import Base
from utils.Constants import *


class WordNetWrapper(Base):

    accepted_forward_links = []
    accepted_AMOD_list = []

    def __init__(self):
        nltk.download('wordnet')

        for word in f_acceptedAMODforLoops:
            synsets = wn.synsets(word, POS_ADJECTIVE)
            for synset in synsets:
                for lemma in synset.lemma_names():
                    self.accepted_AMOD_list.append(lemma)

            synsets = wn.synsets(word, POS_ADVERB)
            for synset in synsets:
                for lemma in synset.lemma_names():
                    self.accepted_AMOD_list.append(lemma)

        for word in f_acceptedForForwardLink:
            synsets = wn.synsets(word, POS_ADJECTIVE)
            for synset in synsets:
                for lemma in synset.lemma_names():
                    self.accepted_forward_links.append(lemma)

            synsets = wn.synsets(word, POS_ADVERB)
            for synset in synsets:
                for lemma in synset.lemma_names():
                    self.accepted_forward_links.append(lemma)

    def person_or_system(self, full_noun, main_noun):
        full_noun = full_noun.lower()
        if full_noun in f_personCorrectorList or full_noun in f_personPronouns:
            return True

        synsets = wn.synsets(full_noun, POS_NOUN)
        if len(synsets) == 0 or main_noun not in synsets[0].lemma_names():
            synsets = wn.synsets(main_noun, POS_NOUN)

        if len(synsets) > 0:
            return self.check_hypernym_tree(synsets, f_realActorDeterminers)
        else:
            self.logger.error("Could not find Person or System {} and {}".format(full_noun, main_noun))
            return False

    def can_be_group_action(self, main_noun):
        synsets = wn.synsets(main_noun, POS_NOUN)
        if len(synsets) > 0:
            return self.check_hypernym_tree(synsets, [GROUP_ACTION])
        else:
            self.logger.error("Could not find group action noun {}".format(main_noun))
            return False

    def is_meta_actor(self, full_noun, noun):
        if full_noun not in f_personCorrectorList:
            synsets = wn.synsets(full_noun, POS_NOUN)
            if len(synsets) == 0 or noun not in synsets[0].lemma_names():
                synsets = wn.synsets(noun, POS_NOUN)

            if len(synsets) > 0:
                return self.check_hypernym_tree(synsets, f_metaActorsDeterminers)
            else:
                self.logger.error("Could not find Meta Actor {} and {}".format(full_noun, noun))

        return False

    def is_weak_action(self, action):
        if self.is_weak_verb(action.f_name):
            return not action.f_xcomp or self.is_weak_verb(action.f_xcomp.f_name)
        else:
            return False

    def is_verb_of_type(self, verb, verb_type):
        synsets = wn.synsets(verb, POS_VERB)
        if len(synsets) > 0:
            return self.check_hypernym_tree(synsets, [verb_type])
        else:
            self.logger.error("Could not find Verb {} of type {}".format(verb, verb_type))
            return False

    def is_weak_verb(self, name):
        return self.get_base_form(name) in f_weakVerbs

    def get_base_form(self, name, keep_auxiliars=True, pos_tag=POS_VERB):
        words = name.split()
        synsets = wn.synsets(words[-1], pos_tag)
        base_form = ""

        if len(synsets) > 0:
            if keep_auxiliars:
                for word in words[:-1]:
                    base_form += word + " "

            base_form += words[-1].lemma_names[0]
            return base_form
        else:
            self.logger.error("Could not find base form of {}".format(name))
            return name

    def is_time_period(self, word):
        synsets = wn.synsets(word, POS_NOUN)
        if len(synsets) > 0:
            return self.check_hypernym_tree(synsets, [TIME_PERIOD])
        else:
            self.logger.error("Could not find time period {}".format(word))
            return False

    @staticmethod
    def derive_verb(word):
        synsets = wn.synsets(word, POS_NOUN)
        derived_verb = None
        lowest_distance = 0
        for synset in synsets:
            for lemma in synset.lemmas():
                for derived_lemma in lemma.derivationally_related_forms():
                    if derived_lemma.synset().pos() == POS_VERB:
                        distance = edit_distance(derived_lemma.name(), word)
                        if not derived_verb or distance < lowest_distance:
                            derived_verb = derived_lemma.name()
                            lowest_distance = distance

        return derived_verb

    def check_hypernym_tree(self, synsets, word_list):
        for synset in synsets:
            if len(synset.instance_hypernyms()) == 0:
                if self.can_be(synset, word_list, []):
                    return True

        return False

    def can_be(self, synset, word_list, checked):
        if synset not in checked:
            checked.append(synset)
            for word in word_list:
                if word.lower() in synset.lemma_names():
                    return True

            for hypernym in synset.hypernyms():
                if self.can_be(hypernym, word_list, checked):
                    return True

        return False


WordNetWrapper = WordNetWrapper()
