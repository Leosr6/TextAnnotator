from data.SentenceElements import Action


class ConjunctionElement:
    f_to = None
    f_from = None
    f_type = ""


class Flow:
    f_multiples = []
    f_single = None
    f_type = ""
    f_direction = ""
    f_sentence = None

    def __init__(self, sentence):
        self.f_sentence = sentence


class DummyAction(Action):

    def __init__(self, action=None):
        if action:
            super().__init__(action.f_sentence, action.f_word_index + 1, "Dummy node")
        else:
            super().__init__(None, -1, "Dummy node")
