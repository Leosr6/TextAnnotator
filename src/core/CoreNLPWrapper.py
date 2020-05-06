"""
    Wraps the CoreNLP classes to use the enhancedDependencies of the
    dependency parser without the extra dependencies
"""

from nltk.parse.corenlp import GenericCoreNLPParser
from nltk.tree import ParentedTree
import xmltodict as xml
import json
from utils.Constants import SPEC_SPLIT, PUNCT


class CoreNLPWrapper(GenericCoreNLPParser):

    def make_deps(self, dependencies):
        result = []

        for dep in dependencies:
            parsed_dep = dep['@type'].split(SPEC_SPLIT)
            if parsed_dep[0] != PUNCT and '@extra' not in dep:
                result.append({
                    'dep': parsed_dep[0], 'spec': parsed_dep[1] if len(parsed_dep) > 1 else "",
                    'dependent': int(dep['dependent']['@idx']), 'dependentGloss': dep['dependent']['#text'].lower(),
                    'governor': int(dep['governor']['@idx']), 'governorGloss': dep['governor']['#text'].lower()
                })

        return result

    def create_raw_sentence(self, tokens):
        tokens_map = {
            '-LRB-': '(',
            '-RRB-': ')',
            '-LSB-': '[',
            '-RSB-': ']',
            '-LCB-': '{',
            '-RCB-': '}',
            '``': '"',
            '\'\'': '"'
        }

        raw_sentence = ""

        for token in tokens:
            word = token["word"]
            raw_sentence += tokens_map.get(word, word) + " "

        return raw_sentence[:-1] if len(raw_sentence) > 0 else raw_sentence


    def parse_text(self, text):
        default_properties = {
            'outputFormat': 'xml',
            'annotators': 'tokenize,pos,lemma,ssplit,parse,depparse'
        }

        response = self.session.post(
            self.url,
            params={'properties': json.dumps(default_properties)},
            data=text.encode(self.encoding),
            timeout=60
        )

        response.raise_for_status()

        parsed_data = xml.parse(response.text)
        sentences = parsed_data['root']['document']['sentences']['sentence']
        sentences = sentences if isinstance(sentences, list) else [sentences]

        for sentence in sentences:
            yield (ParentedTree.fromstring(sentence['parse'],
                                           read_leaf=lambda leaf: leaf.lower(),
                                           read_node=lambda node: node.split("-")[0]),
                   self.make_deps(sentence['dependencies'][3]['dep']),
                   self.create_raw_sentence(sentence['tokens']['token']))
