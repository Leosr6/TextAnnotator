class StanfordSentence:

    def __init__(self, tree, dependencies, raw_sentence, sentence_id):
        self.f_tree = tree
        self.f_dependencies = dependencies
        self.raw_sentence = raw_sentence
        self.f_id = sentence_id

    def __str__(self):
        return self.raw_sentence
