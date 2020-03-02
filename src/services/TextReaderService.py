from nltk.parse.corenlp import CoreNLPServer

class TextReaderService:

    def __init__(self):
        # Not working
        # server = CoreNLPServer(corenlp_options=['-serverProperties',
        #                                         '/resources/stanford-corenlp-full-2018-10-05/StanfordCoreNLP-test.properties'],
        #                        path_to_jar='C:/Users/LEOSR/PycharmProjects/TextToBPM/resources/stanford-corenlp-full-2018-10-05/stanford-corenlp-3.9.2.jar',
        #                        path_to_models_jar='C:/Users/LEOSR/PycharmProjects/TextToBPM/resources/stanford-corenlp-full-2018-10-05/stanford-corenlp-3.9.2-models.jar',
        #                        verbose=True,
        #                        java_options='-Xmx4g -cp "*"'
        #                        )
        # server.start()

        # Execute the following JAVA Command Line from the folder /resources/stanford-corenlp-full-2018-10-05
        # java -Xmx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -preload tokenize,ssplit,pos,parse