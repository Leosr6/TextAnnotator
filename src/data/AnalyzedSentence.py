class AnalyzedSentence:

    # TO-DO: check this parameter
    f_ignoreNPSubSentences = True
    f_sentence = ""
    f_sentenceNumber = 0
    f_root = None
    f_sentenceTags = []
    f_conjs = []
    f_actions = []

    def __init__(self, sentence, root, snumber):
        self.f_sentence = sentence
        self.f_root = root
        self.f_sentenceNumber = snumber
        self.f_conjs = []
        self.f_actions = []
