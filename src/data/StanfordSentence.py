class StanfordSentence:

    def __init__(self, tree, dependencies, tokens, sentence_id):
        # TODO: check ids
        self.f_lastID = 0
        # TODO: check offset
        self.f_offset = 0
        self.f_tokens = tokens
        self.f_tree = tree
        self.f_dependencies = dependencies
        self.f_id = sentence_id

    def __str__(self):
        return " ".join(self.f_tree.leaves())
