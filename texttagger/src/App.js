import React, { useState, useEffect, useRef } from 'react';
import { Card, CardBody, CardFooter, CardHeader,
          Col, Form, FormGroup, Input, Label, Row,
          Button, CustomInput } from 'reactstrap';
import "./App.css";

const precedence = ["startevent", "endevent", "activity", "xorjoin", "xorsplit"]
const stdColor = "black"

function App() {
  const [text, setText] = useState("");
  const [markedText, setMarkedText] = useState([]);
  const [selectedMakers, setSelectedMarkers] = useState({
    "activity" : {marker : "Activity", color : "red", checked : false},
    "startevent" : {marker : "Start Event", color : "yellow", checked : false},
    "xorsplit" : {marker : "XOR-Split", color : "darkblue", checked : false},
    "xorjoin" : {marker : "XOR-Join", color : "lightblue", checked : false}
  });
  const [useFile, setUseFile] = useState(false);
  const [disabledButton, setDisabledButton] = useState(false);
  const [metadata, setMetadata] = useState({});
  const textFile = useRef();

  useEffect(() => {
    var text = [];

    if (metadata.text) {
      for (var sentence of metadata.text.values()) {
        var typeMap = {};

        for (var snippet of sentence.snippetList.values()) {
          var elementType = snippet.processElementType.toLowerCase();
          var markerData = selectedMakers[elementType];

          if (markerData && markerData.checked) {
            for (var wordIndex = snippet.startIndex; wordIndex <= snippet.endIndex; wordIndex++) {
              var currentMap = typeMap[wordIndex];
              if (!currentMap || precedence.indexOf(currentMap) > precedence.indexOf(elementType))
                typeMap[wordIndex] = elementType;
            }
          }
        }

        var words = sentence.value.split(" ")

        for (var wordIndex = 0; wordIndex < words.length; wordIndex++) {
          var color = typeMap[wordIndex] ? selectedMakers[typeMap[wordIndex]].color : stdColor;
          text.push({color, word : words[wordIndex]});
        }
      }
    }

    setMarkedText(text);
  }, [metadata, selectedMakers])

  const setMaker = (e, marker) => {
    var newSelectedMarkers = {...selectedMakers}

    newSelectedMarkers[marker].checked = e.target.checked;
    setSelectedMarkers(newSelectedMarkers);
  }

  const onClickMarkText = () => {
    var data = new FormData()
    if (useFile) {
      if (!textFile.current || textFile.current.files.length === 0) {
        alert("Please select a file or switch to use a text.");
        return;
      }
      else {
        data.append('file', textFile.current.files[0])
      }
    }
    else if (text.length === 0) {
      alert("Text can't be empty")
      return
    }

    setDisabledButton(true);

    fetch("http://localhost:5000", {
      method: 'POST',
      headers: {
        'Accept': 'application/json'
      },
      body: useFile ? data : text,
    })
    .then(response => {
      if (response.ok)
        response.json().then(json => setMetadata(json))
      else
        alert("Could not get a valid response from the server")
    })
    .catch((err) => alert(err))
    .finally(() => setDisabledButton(false));
  }

  return (
    <div className="App">
      <Row className="w-100 d-flex justify-content-center">
        <Card className="w-75 mt-3">
          <CardHeader>Write any process model or upload a text file</CardHeader>
          <CardBody className="ml-3">
            <Form>
              <FormGroup row>
                <Label for="text">Text Input</Label>
                <Input type="textarea" id="text" value={text} onChange={(e) => setText(e.target.value)}/>
              </FormGroup>
              <FormGroup row>
                <Label for="file">Upload File</Label>
                <Input type="file" id="file" innerRef={textFile} />
              </FormGroup>
            </Form>
          </CardBody>
          <CardFooter className="d-flex">
            <Button color="primary" onClick={onClickMarkText} disabled={disabledButton}>Mark Text</Button>
            <CustomInput type="switch" label="Use file" id="usefile" checked={useFile} onChange={(e) => setUseFile(e.target.checked)} className="ml-auto"/>
          </CardFooter>
        </Card>
      </Row>
      <div className="d-flex mt-3">
        <Col xs="3">
          <Card>
            <CardHeader>Markers</CardHeader>
            <CardBody>
              {Object.entries(selectedMakers).map((marker) =>
                <div className="d-flex">
                  <div className="colorbox" style={{backgroundColor : marker[1].color}}/>
                  <CustomInput type="switch" label={marker[1].marker} id={marker[0]} 
                                checked={marker[1].checked} onChange={(e) => setMaker(e, marker[0])}/>
                </div>
              )}  
            </CardBody>
          </Card>
        </Col>
        <Col xs="9" className="">
          <Card>
            <CardHeader>Marked Text</CardHeader>
            <CardBody>
              {markedText.map((wordData) => 
                <font color={wordData.color} style={{fontWeight : wordData.color == stdColor ? "normal" : "bold"}}>{wordData.word} </font>
              )}
            </CardBody>
          </Card>
        </Col>
      </div>
    </div>
  );
}

export default App;
