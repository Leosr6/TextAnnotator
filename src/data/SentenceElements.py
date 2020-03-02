class Element:

    f_word_index = -1
    f_name = ""
    f_sentence = None

    def __init__(self, sentence, index, word):
        self.f_sentence = sentence
        self.f_word_index = index
        self.f_word_index = word


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

    def __init__(self, sentence, index, verb):
        super().__init__(sentence, index, verb)


class Actor(Element):

    f_unreal = False
    f_metaActor = False
    f_passive = False
    f_name = ""

    def __init__(self, sentence, index, subj):
        super().__init__(sentence, index, subj)


class Resource(Element):

    f_wordIndex = -1
    f_name = ""
    f_origin = None  # Stanford Sentence
