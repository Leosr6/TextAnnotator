import React, { useState, useEffect } from 'react';
import { Card, CardBody, CardFooter, CardHeader,
          Col, Nav, NavItem, Input, NavLink,
          Button, CustomInput, TabContent, TabPane } from 'reactstrap';
import Dropzone from './Dropzone'
import "./App.css";
import { Icon } from '@iconify/react';
import arrowBackCircleOutline from '@iconify/icons-ion/arrow-back-circle-outline';
import classnames from 'classnames';

const precedence = ["startevent", "endevent", "xorjoin", "andjoin", "orjoin", "xorsplit", "andsplit", "orsplit", "eventbasedgateway", "intermediateevent", "activity"]
const stdColor = "black"

function App() {
  const [text, setText] = useState("");
  const [markedText, setMarkedText] = useState([]);
  const [selectedMakers, setSelectedMarkers] = useState({
    "activity" : {marker : "Activity", color : "blue", checked : false},
    "startevent" : {marker : "Start Event", color : "lime", checked : false},
    "endevent" : {marker : "End Event", color : "red", checked : false},
    "intermediateevent" : {marker : "Intermediate Event", color : "orange", checked : false},
    "xorsplit" : {marker : "XOR-Split", color : "darkblue", checked : false},
    "xorjoin" : {marker : "XOR-Join", color : "darkblue", checked : false},
    "andsplit" : {marker : "AND-Split", color : "darkgreen", checked : false},
    "andjoin" : {marker : "AND-JOIN", color : "darkgreen", checked : false},
    "orsplit" : {marker : "OR-SPLIT", color : "chocolate", checked : false},
    "orjoin" : {marker : "OR-JOIN", color : "chocolate", checked : false},
    "eventbasedgateway" : {marker : "Event-based Gateway", color : "brown", checked : false}
  });
  const [disabledButton, setDisabledButton] = useState(false);
  const [metadata, setMetadata] = useState({});
  const [activeTab, setActiveTab] = useState("2");
  const [inputTab, setInputTab] = useState("1-a");
  const [textFile, setTextFile] = useState(null);
  const [actors, setActors] = useState([]);

  useEffect(() => {
    var text = [];

    if (metadata.text) {
      for (var sentence of metadata.text.values()) {
        var typeMap = {};

        for (var snippet of sentence.snippetList.values()) {
          var elementType = snippet.processElementType.toLowerCase();
          var actor = sentence.processList[0].resourceList.find((resource) => snippet.resourceId === resource.id)
          var markerData = selectedMakers[elementType];

          if (markerData && markerData.checked) {
            for (var wordIndex = snippet.startIndex -1; wordIndex <= snippet.endIndex -1; wordIndex++) {
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
    const useFile = inputTab === "1-b"

    if (useFile) {
      if (textFile) {
        data.append('file', textFile)
      }
      else {
        alert("Please select a file or switch to use a text.");
        return;
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
      if (response.ok) {
        response.json().then(json => setMetadata(json))
        setActiveTab("2")
      }
      else
        alert("Could not get a valid response from the server")
    })
    .catch((err) => alert(err))
    .finally(() => setDisabledButton(false));
  }

  const handleDropAccepted = (files) => {
    setTextFile(files[0]);
  }

  return (
    <div className="App">
      <TabContent activeTab={activeTab} className="h-100">
        <TabPane tabId="1" className="h-100">
            <div className="h-100 d-flex justify-content-center" style={{paddingTop : "5%"}}>
              <Card className="w-75" style={{height : "85%"}}>
                <CardHeader>Write any process model or upload a text file</CardHeader>
                <CardBody className="ml-3">
                  <Nav tabs>
                    <NavItem>
                      <NavLink className={classnames({ active: inputTab === '1-a' })} onClick={() => { setInputTab('1-a'); }}>
                        Text Input
                      </NavLink>
                    </NavItem>
                    <NavItem>
                      <NavLink className={classnames({ active: inputTab === '1-b' })} onClick={() => { setInputTab('1-b'); }}>
                        File Input
                      </NavLink>
                    </NavItem>
                  </Nav>
                  <TabContent activeTab={inputTab} style={{height : "85%", marginTop : "1em"}}>
                    <TabPane tabId="1-a" className="h-100">
                      <Input type="textarea" className="h-100" id="text" value={text} onChange={(e) => setText(e.target.value)}/>
                    </TabPane>
                    <TabPane tabId="1-b" className="h-100">
                      <Dropzone handleDropAccepted={handleDropAccepted}/>
                    </TabPane>
                  </TabContent>
                </CardBody>
                <CardFooter className="d-flex">
                  <Button color="primary" onClick={onClickMarkText} disabled={disabledButton}>Mark Text</Button>
                </CardFooter>
              </Card>
            </div>
        </TabPane>
        <TabPane tabId="2" className="h-100">
          <div className="h-100 d-flex justify-content-center" style={{paddingTop : "5%"}}>
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
              <Card className="mt-3">
                <CardHeader>Actors</CardHeader>
                <CardBody>
                </CardBody>
              </Card>
            </Col>
            <Col xs="8" className="">
              <Card>
                <CardHeader>Marked Text</CardHeader>
                <CardBody>
                  {markedText.map((wordData, index) =>
                    <font key={index} color={wordData.color} style={{fontWeight : wordData.color === stdColor ? "normal" : "bold"}}>{wordData.word} </font>
                  )}
                </CardBody>
                <CardFooter>
                  <Button outline color="primary" size="sm" onClick={() => setActiveTab("1")}>
                    <Icon icon={arrowBackCircleOutline} width="20" height="20" className="mr-2"/>
                    Change Text
                  </Button>
                </CardFooter>
              </Card>
            </Col>
          </div>
        </TabPane>
      </TabContent>
    </div>
  );
}

export default App;
