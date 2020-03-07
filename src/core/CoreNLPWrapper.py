"""
    Wraps the CoreNLP classes to use the enhancedPlusPlusDependencies of the
    dependency parser instead of the basicDependencies
"""

from nltk.parse import corenlp


def transform(sentence):
    for dependency in sentence['enhancedPlusPlusDependencies']:
        dependent_index = dependency['dependent']
        token = sentence['tokens'][dependent_index - 1]

        # Return values that we don't know as '_'. Also, consider tag and ctag
        # to be equal.
        yield (
            '_',
            str(dependent_index),
            token['word'],
            token['lemma'],
            token['pos'],
            token['pos'],
            '_',
            str(dependency['governor']),
            dependency['dep'],
            '_',
            '_',
        )


corenlp.transform = transform
CoreNLPParser = corenlp.CoreNLPParser
CoreNLPDependencyParser = corenlp.CoreNLPDependencyParser


class CoreNLPWrapper(CoreNLPParser, CoreNLPDependencyParser):

    def parse_text(self, text):
        parsed_data = self.api_call(text)

        for sentence in parsed_data['sentences']:
            yield (CoreNLPParser.make_tree(self, sentence),
                   sentence['enhancedPlusPlusDependencies'],
                   #CoreNLPDependencyParser.make_tree(self, sentence),
                   sentence['tokens'])
