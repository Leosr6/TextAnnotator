from core.CoreNLPWrapper import CoreNLPWrapper
from data.WorldModel import WorldModel
from core.SentenceAnalyzer import SentenceAnalyzer
from data.StanfordSentence import StanfordSentence

class TextAnalyzer:

    f_world = None
    f_text = ""
    f_parser = None

    def __init__(self, **kwargs):

        self.f_world = WorldModel()
        self.f_parser = CoreNLPWrapper()

    def analyze_text(self, text):

        self.f_text = text
        sentence_analyzer = SentenceAnalyzer(self.f_world)

        sentences = self.create_stanford_sentences(text)

        for stanford_sentence in sentences:
            sentence_analyzer.analyze_sentence(stanford_sentence)

    def create_stanford_sentences(self, text):

        # List of standford_sentences
        stanford_sentences = []

        sentences = self.f_parser.parse_text(text)

        for sentence in sentences:
            tree, deps, tokens = sentence
            s_sentence = StanfordSentence(tree, deps, tokens)
            stanford_sentences.append(s_sentence)

        return stanford_sentences
