class Element:

    f_word_index = -1
    f_name = ""
    f_sentence = None
    f_specifiers = []

    def __init__(self, sentence, index, word):
        self.f_sentence = sentence
        self.f_word_index = index
        self.f_name = word
        self.f_specifiers = []

    def get_specifiers(self, types):
        # TO-DO: EQUAL COMP ONLY WORKS IF REFERENCE IS THE SAME
        return [spec for spec in self.f_specifiers if spec.f_type in types]


class ExtractedObject(Element):

    f_subjectRole = True
    f_determiner = None
    f_reference = None
    f_needsResolve = False


class Specifier(Element):

    f_type = None#SpecifierType.DIRECT
    f_headWord = None
    f_object = None
    f_pt = None#PhraseType.UNKNOWN
    f_fe = None

    # def __init__(self, sentence, index, phrase):
    #     super().__init__(sentence, index, phrase)


class Action(Element):

    f_baseForm = None

    f_actorFrom = None
    f_object = None

    f_xcomp = None


    f_prt = None
    f_cop = None
    f_copIndex = None
    f_aux = None

    f_mod = None
    f_modPos = -1

    f_marker = None
    f_markerFromPP = False
    f_preAdvMod = None
    f_preAdvModPos = -1
    f_prepc = None
    f_negated = False

    f_link = None
    f_linkType = None
    f_transient = False

    # def __init__(self, sentence, index, verb):
    #     super().__init__(sentence, index, verb)


class Actor(ExtractedObject):

    f_unreal = False
    f_metaActor = False
    f_passive = False

    # def __init__(self, sentence, index, subj):
    #     super().__init__(sentence, index, subj)


class Resource(ExtractedObject):
    pass
