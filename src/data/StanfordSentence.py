class StanfordSentence:

    # TO-DO: check ids
    f_lastID = 0
    f_id = 0
    f_tree = None
    f_dependencies = []
    f_offset = 0
    f_tokens = []

    def __init__(self, tree, dependencies, tokens):
        self.f_tokens = tokens
        self.f_tree = tree
        self.f_dependencies = dependencies
