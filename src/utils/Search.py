from collections import Counter
from functools import reduce


def count_children(sentence, types):
    counter = Counter([child.label() for child in list(sentence)])
    return reduce(lambda a, b: a + counter[b], types, 0)


def find_children(sentence, types):
    children = [child for child in list(sentence) if child.label() in types]
    return children


def find_dependencies(dependencies, types):
    deps = [dep for dep in dependencies if dep['dep'] in types]
    return deps


def find_sentence_index(fsentence, sentence):
    array = fsentence.leaves()
    part = sentence.leaves()
    indices = [i for i in range(len(array)) if array[i:i+len(part)] == part]
    return indices[0]


def find_dep_in_tree(fsentence, dep_index):
    tree_path = list(fsentence.leaf_treeposition(dep_index))
    return fsentence[tree_path[:-1]]


def filter_by_gov(dependencies, gov_index):
    deps = [dep for dep in dependencies
            if gov_index == dep['governor']]
    return deps


def get_full_phrase_tree(tree_node, type):
    node = tree_node
    while node and node.label() != type and node.label()[0] != "W":
        node = node.parent()

    return node


def find_in_tree(tree, types, exclude):
    result = []
    if tree.label() in types:
        result.append(tree)
    for child in list(tree):
        if not isinstance(child, str) and child.label() not in exclude:
            result.extend(find_in_tree(child, types, exclude))

    return result