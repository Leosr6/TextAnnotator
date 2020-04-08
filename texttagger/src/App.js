import React, { useState, useEffect, useRef } from 'react';
import { Card, CardBody, CardFooter, CardHeader,
          Col, Form, FormGroup, Input, Label, Row,
          Button, CustomInput } from 'reactstrap';
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [markedText, setMarkedText] = useState("");
  const [selectedMakers, setSelectedMarkers] = useState([
    {marker : "Activity", color : "red", checked : false},
    {marker : "Start Event", color : "yellow", checked : false},
    {marker : "XOR-Split", color : "darkblue", checked : false},
    {marker : "XOR-Join", color : "lightblue", checked : false}
  ]);
  const [useFile, setUseFile] = useState(false);
  const [disabledButton, setDisabledButton] = useState(false);
  const [metadata, setMetadata] = useState({});
  const textFile = useRef();

  useEffect(() => {
    setMarkedText(JSON.stringify(metadata));
  }, [metadata, selectedMakers])

  const setMaker = (e, index) => {
    var newSelectedMarkers = [...selectedMakers]

    newSelectedMarkers[index].checked = e.target.checked;
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
              {selectedMakers.map((markerData, index) =>
                <div className="d-flex">
                  <div className="colorbox" style={{backgroundColor : markerData.color}}/>
                  <CustomInput type="switch" label={markerData.marker} id={markerData.marker} 
                                checked={markerData.checked} onChange={(e) => setMaker(e, index)}/>
                </div>
              )}  
            </CardBody>
          </Card>
        </Col>
        <Col xs="9" className="">
          <Card>
            <CardHeader>Marked Text</CardHeader>
            <CardBody>
              <Input type="textarea" value={markedText} readOnly style={{height : "20em"}}/>
            </CardBody>
          </Card>
        </Col>
      </div>
    </div>
  );
}

export default App;
