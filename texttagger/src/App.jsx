import React, { useState, useEffect } from 'react';
import { Col, TabContent, TabPane } from 'reactstrap';
import "./App.css";
import InputSection from './Components/InputSection';
import OutputSection from './Components/OutputSection';
import Markers from './Components/Markers';
import Actors from './Components/Actors'

function App() {
  const [selectedMarkers, setSelectedMarkers] = useState({});
  const [metadata, setMetadata] = useState({});
  const [activeTab, setActiveTab] = useState("input");
  const [textResources, setTextResources] = useState([]);

  useEffect(() => {
    if (metadata.resourceList)
      setTextResources(metadata.resourceList);
  }, [metadata])

  const handleMarkedTextResponse = (json) => {
    setMetadata(json);
    setActiveTab("output");
  }

  return (
    <div className="App">
      <TabContent activeTab={activeTab} className="h-100">
        <TabPane tabId="input" className="h-100">
            <div className="h-100 d-flex justify-content-center" style={{paddingTop : "5%"}}>
              <InputSection handleMarkedText={handleMarkedTextResponse}/>
            </div>
        </TabPane>
        <TabPane tabId="output" className="h-100">
          <div className="h-100 d-flex justify-content-center" style={{paddingTop : "5%"}}>
            <Col xs="3">
              <Markers handleMarkerChange={setSelectedMarkers}/>
              <Actors textResources={textResources}/>
            </Col>
            <Col xs="8" className="">
              <OutputSection metadata={metadata} selectedMarkers={selectedMarkers} textResources={textResources} handleChangeText={() => setActiveTab("input")}/>
            </Col>
          </div>
        </TabPane>
      </TabContent>
    </div>
  );
}

export default App;
