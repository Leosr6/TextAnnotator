class AnalyzedSentence:

    f_sentence = ""
    f_root = None
    f_conjs = []
    f_actions = []

    def __init__(self, sentence, root):
        self.f_sentence = sentence
        self.f_root = root
        self.f_conjs = []
        self.f_actions = []
