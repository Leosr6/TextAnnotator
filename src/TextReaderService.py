from nltk.parse.corenlp import CoreNLPServer
import json
from flask import Flask, request, make_response
from core.TextAnalyzer import TextAnalyzer
from core.ProcessModelBuilder import ProcessModelBuilder


app = Flask(__name__)
ALLOWED_EXTENSIONS = {'txt'}

# Starting the CoreNLP Server
server = CoreNLPServer(corenlp_options=['-serverProperties',
                                        'C:/Users/LEOSR/PycharmProjects/TextToBPM/resources/stanford-corenlp-full-2018-10-05/StanfordCoreNLP-test.properties'],
                       path_to_jar='C:/Users/LEOSR/PycharmProjects/TextToBPM/resources/stanford-corenlp-full-2018-10-05/stanford-corenlp-3.9.2.jar',
                       path_to_models_jar='C:/Users/LEOSR/PycharmProjects/TextToBPM/resources/stanford-corenlp-full-2018-10-05/stanford-corenlp-3.9.2-models.jar',
                       verbose=True,
                       java_options='-Xmx4g')
server._classpath = 'C:/Users/LEOSR/PycharmProjects/TextToBPM/resources/stanford-corenlp-full-2018-10-05/*'
server.start()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/textreader", methods=["POST"])
def TextReaderService():
    text = None

    # Checks if the user uploaded a file or a text
    file = request.files.get("file", None)
    if file and allowed_file(file.filename):
        text = file.read()
    elif request.content_type == "text/plain":
        text = request.get_data(as_text=True)

    if text:
        try:
            bpmn = text_to_bpmn(text)
            return make_response((str({"nodes": bpmn.f_nodes, "edges": bpmn.f_edges,
                                       "flow_objects": bpmn.f_flow_objects,
                                       "flows": bpmn.f_flows}), 200))
        except Exception as e:
            return make_response((str(e), 500))
    else:
        return make_response(("Could not read text format", 400))


def text_to_bpmn(text):
    text_analyzer = TextAnalyzer()
    model_builder = ProcessModelBuilder()

    f_world = text_analyzer.analyze_text(text)
    f_model = model_builder.create_process_model(f_world)

    return f_model

