import spacy
from time import time
from utils.Exceptions import PipeRequiredException


class SentenceAnalyzer

    f_world = None
    f_sentenceNumber = time()
    nlp = None
    required_pipes = ["tagger", "parser", "ner"]

    def __init__(self, world_model, **kwargs):

        nlp = kwargs.get("nlp", spacy.load("en_core_web_sm"))

        for pipe in self.required_pipes:
            if not nlp.has_pipe(pipe):
                raise PipeRequiredException(pipe)

        self.f_world = world_model
        self.nlp = nlp

    def analyze_sentence(self, sentence):

        nlp = self.nlp
        f_root = nlp(sentence)
        self.f_sentenceNumber += 1

        analyzedSentence = AnalyzedSentence(sentence, f_root, f_sentenceNumber)
        return analyzedSentence

