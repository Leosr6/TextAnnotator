from nltk.tree import ParentedTree


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
        self.f_tree = ParentedTree.convert(tree)
        self.f_dependencies = dependencies

    """
        Iterates over all nodes of the dependency graph and
        concatenate their dependencies in a list
    """
    # def get_typed_dependencies(self):
    #     dependencies = []
    #
    #     for node in self.f_graph.values():
    #         deps = node['deps']
    #         for dep_type in deps:
    #             for dep_index in deps[dep_type]:
    #                 dependencies.append({'word': self.f_graph[dep_index]['word'],
    #                                      'dep': self.f_graph[dep_index],
    #                                      'rel': dep_type})
    #
    #     return dependencies
