from utils.Constants import UNKNOWN, DIRECT
from core.WordNetWrapper import WordNetWrapper


class ConjunctionElement:

    def __init__(self, el_from, el_to, conj):
        self.f_from = el_from
        self.f_to = el_to
        self.f_type = conj


class Element:

    def __init__(self, sentence, index, word):
        self.f_sentence = sentence
        self.f_word_index = index
        self.f_name = word or ""
        self.f_specifiers = []

    def get_specifiers(self, types):
        types = (types,) if isinstance(types, str) else types
        return [spec for spec in self.f_specifiers if spec.f_type in types]


class ExtractedObject(Element):

    def __init__(self, sentence, index, word):
        super().__init__(sentence, index, word)
        self.f_subjectRole = True
        self.f_determiner = None
        self.f_reference = None
        self.f_needsResolve = False


class Specifier(Element):

    def __init__(self, sentence, index, word):
        super().__init__(sentence, index, word)
        self.f_type = DIRECT
        self.f_headWord = ""
        self.f_object = None
        self.f_pt = UNKNOWN
        self.f_fe = None


class Action(Element):

    def __init__(self, sentence, index, word):
        super().__init__(sentence, index, word)
        self.f_baseForm = WordNetWrapper.get_base_form(word)
        self.f_actorFrom = None
        self.f_object = None
        self.f_xcomp = None
        self.f_prt = None
        self.f_cop = None
        self.f_copIndex = None
        self.f_aux = None
        self.f_mod = None
        self.f_modPos = -1
        self.f_marker = None
        self.f_markerFromPP = False
        self.f_preAdvMod = None
        self.f_preAdvModPos = -1
        self.f_prepc = None
        self.f_negated = False
        self.f_link = None
        self.f_linkType = None
        self.f_transient = False


class Actor(ExtractedObject):

    def __init__(self, sentence, index, word):
        super().__init__(sentence, index, word)
        self.f_unreal = False
        self.f_metaActor = False
        self.f_passive = False


class Resource(ExtractedObject):
    pass
