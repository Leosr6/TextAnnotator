from data.SentenceElements import Action
from utils.Constants import DUMMY_NODE, SPLIT


class Flow:

    def __init__(self, sentence):
        self.f_multiples = []
        self.f_single = None
        self.f_type = ""
        self.f_direction = SPLIT
        self.f_sentence = sentence


class DummyAction(Action):

    def __init__(self, action=None):
        if action:
            super().__init__(action.f_sentence, action.f_word_index + 1, DUMMY_NODE, action.label)
        else:
            super().__init__(None, -1, DUMMY_NODE, None)
