import atexit
from socket import error
import json
from nltk.parse.corenlp import CoreNLPServer
from flask import Flask, request, make_response
from core.TextGenerator import TextGenerator
from core.TextAnalyzer import TextAnalyzer
from core.ProcessModelBuilder import ProcessModelBuilder


app = Flask(__name__)
ALLOWED_EXTENSIONS = {'txt'}

# Starting the CoreNLP Server
try:
    server = CoreNLPServer(corenlp_options=['-serverProperties',
                                            'C:/Users/LEOSR/PycharmProjects/TextToBPM/resources/stanford-corenlp-full-2018-10-05/StanfordCoreNLP-test.properties'],
                           path_to_jar='C:/Users/LEOSR/PycharmProjects/TextToBPM/resources/stanford-corenlp-full-2018-10-05/stanford-corenlp-3.9.2.jar',
                           path_to_models_jar='C:/Users/LEOSR/PycharmProjects/TextToBPM/resources/stanford-corenlp-full-2018-10-05/stanford-corenlp-3.9.2-models.jar',
                           verbose=True,
                           java_options='-Xmx4g',
                           port=9000)
    server._classpath = 'C:/Users/LEOSR/PycharmProjects/TextToBPM/resources/stanford-corenlp-full-2018-10-05/*'
    server.start()
    atexit.register(server.stop)
except error:
    print("Something is already running on port 9000.")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/textreader", methods=["POST"])
def TextReaderService():
    text = None

    # Checks if the user uploaded a file or a text
    file = request.files.get("file")
    if file and allowed_file(file.filename):
        text = file.read()
    elif request.content_type == "text/plain":
        text = request.get_data(as_text=True)

    if text:
        try:
            metadata = generate_metadata(text)
            return make_response((json.dumps(metadata), 200, {"Content-Type": "application/json"}))
        except Exception as e:
            return make_response((str(e), 500))
    else:
        return make_response(("Could not read text format", 400))


def generate_metadata(text):
    text_analyzer = TextAnalyzer()
    f_world = text_analyzer.analyze_text(text)

    model_builder = ProcessModelBuilder(f_world)
    model_builder.create_process_model()

    text_generator = TextGenerator(text_analyzer, model_builder)

    return text_generator.create_metadata()
