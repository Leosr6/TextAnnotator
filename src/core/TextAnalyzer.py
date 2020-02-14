from spacy.pipeline import Sentencizer
from data import WorldModel
import SentenceAnalyzer

class TextAnalyzer:

    f_world = None
    f_text = ""
    nlp = None

    def __init__(self, **kwargs):

        nlp = kwargs.get("nlp", spacy.load("en_core_web_sm"))

        self.f_world = WorldModel()
        self.nlp = nlp

    def analyze_text(self, text):

        self.f_text = text

        sentence_analyzer = SentenceAnalyzer(self.f_world, self.nlp)
        sentences = self.get_sentences()

        for sent in sentences:
            sentence_analyzer.analyze_sentence(sent)

    def get_sentences(self, text):
        sentencizer = Sentencizer()
        nlp = self.nlp

        # Disable all other pipes and apply only the sentencizer
        with nlp.disable_pipes(nlp.pipe_names):
            nlp.add_pipe(sentencizer)
            sents = nlp(text).sents
            nlp.remove_pipe(sentencizer.name)

        return list(sents)
