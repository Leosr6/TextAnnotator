"""
    Wraps the CoreNLP classes to use the enhancedPlusPlusDependencies of the
    dependency parser instead of the basicDependencies
"""

from nltk.parse.corenlp import CoreNLPParser

class CoreNLPWrapper(CoreNLPParser):

    def parse_text(self, text):
        parsed_data = self.api_call(text)

        for sentence in parsed_data['sentences']:
            yield (self.make_tree(sentence),
                   sentence['enhancedPlusPlusDependencies'],
                   sentence['tokens'])
