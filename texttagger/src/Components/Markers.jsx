import React, { useState, useEffect } from 'react';
import { Card, CardBody, CardHeader,
          Button, CustomInput, Modal,
          ModalHeader, ModalBody, ModalFooter } from 'reactstrap';
import { SketchPicker } from 'react-color';
import gatewayXor from '@iconify/icons-bpmn/gateway-xor';
import gatewayOr from '@iconify/icons-bpmn/gateway-or';
import gatewayParallel from '@iconify/icons-bpmn/gateway-parallel';
import taskIcon from '@iconify/icons-bpmn/task';
import startEvent from '@iconify/icons-bpmn/start-event';
import endEvent from '@iconify/icons-bpmn/end-event';
import userIcon from '@iconify/icons-bpmn/user';
import intermediateEvent from '@iconify/icons-bpmn/intermediate-event';
import intermediateEventCatchTimer from '@iconify/icons-bpmn/intermediate-event-catch-timer';
import intermediateEventCatchCondition from '@iconify/icons-bpmn/intermediate-event-catch-condition';
import intermediateEventCatchMessage from '@iconify/icons-bpmn/intermediate-event-catch-message';
import intermediateEventCatchError from '@iconify/icons-bpmn/intermediate-event-catch-error';
// import intermediateEventThrowMessage from '@iconify/icons-bpmn/intermediate-event-throw-message';


function Markers(props) {
    const {handleMarkerChange} = props;
  const [selectedMarkers, setSelectedMarkers] = useState({
    "lane" : {marker : "Lane", color : "darkgreen", checked : false, icon : userIcon},
    "task" : {marker : "Task", color : "red", checked : false, icon : taskIcon},
    "startevent" : {marker : "Start Event", color : "lime", checked : false, icon : startEvent},
    "endevent" : {marker : "End Event", color : "#442727", checked : false, icon : endEvent},
    "errorintermediateevent" : {marker : "Error Event", color : "#d1d63b", checked : false, icon : intermediateEventCatchError},
    "intermediateevent" : {marker : "Intermediate Event", color : "orange", checked : false, icon : intermediateEvent},
    "conditionalintermediateevent" : {marker : "Conditional Event", color : "#b36200", checked : false, icon : intermediateEventCatchCondition},
    "timerintermediateevent" : {marker : "Timer Event", color : "#222831", checked : false, icon : intermediateEventCatchTimer},
    "messageintermediateevent" : {marker : "Message Event", color : "sandybrown", checked : false, icon : intermediateEventCatchMessage},
    "xorsplit" : {marker : "XOR Split", color : "violet", checked : false, icon : gatewayXor},
    "xorjoin" : {marker : "XOR Join", color : "violet", checked : false, icon : gatewayXor},
    "andsplit" : {marker : "AND Split", color : "#588da8", checked : false, icon : gatewayParallel},
    "andjoin" : {marker : "AND Join", color : "#588da8", checked : false, icon : gatewayParallel},
    "orsplit" : {marker : "OR Split", color : "#342ead", checked : false, icon : gatewayOr},
    "orjoin" : {marker : "OR Join", color : "#342ead", checked : false, icon : gatewayOr}
  });
  const [editMarker, setEditMarker] = useState(null);
  const [showAllElements, setShowAllElements] = useState(false);

  useEffect(() => {
    handleMarkerChange(selectedMarkers);
  }, [handleMarkerChange, selectedMarkers])

  const setMaker = (e, marker) => {
    var newSelectedMarkers = {...selectedMarkers};

    newSelectedMarkers[marker].checked = e.target.checked;
    setSelectedMarkers(newSelectedMarkers);
  }

  const onChangeColor = (color, marker) => {
    var newSelectedMarkers = {...selectedMarkers};

    newSelectedMarkers[marker].color = color.hex;
    setSelectedMarkers(newSelectedMarkers);
  }

  const handleShowAllElements = (e) => {
    var newSelectedMarkers = {...selectedMarkers};

    for (var marker in newSelectedMarkers) {
        newSelectedMarkers[marker].checked = e.target.checked;
    }

    setSelectedMarkers(newSelectedMarkers);
    setShowAllElements(e.target.checked);
  }

    return (
        <React.Fragment>
            <Card>
                <CardHeader>Markers</CardHeader>
                <CardBody>
                    <div className="d-flex">
                        <Button className="colorbox" style={{ backgroundColor: "white" }} size="sm" disabled />
                        <CustomInput type="switch" label="All" id="all"
                            checked={showAllElements} onChange={handleShowAllElements} />
                    </div>
                    {Object.entries(selectedMarkers).map((marker) =>
                        <div className="d-flex" key={marker[0]}>
                            <Button className="colorbox" style={{ backgroundColor: marker[1].color }} size="sm" onClick={() => setEditMarker(marker[0])} />
                            <CustomInput type="switch" label={marker[1].marker} id={marker[0]}
                                checked={marker[1].checked} onChange={(e) => setMaker(e, marker[0])} />
                        </div>
                    )}
                </CardBody>
            </Card>
            <Modal isOpen={editMarker ? true : false} style={{ width: 'fit-content' }}>
                <ModalHeader>
                    Change Color
                </ModalHeader>
                <ModalBody>
                    {editMarker &&
                        <SketchPicker color={selectedMarkers[editMarker].color} onChangeComplete={(color, e) => onChangeColor(color, editMarker)} />
                    }
                </ModalBody>
                <ModalFooter>
                    <Button color="primary" size="sm" onClick={() => setEditMarker(null)}>
                        Close
                    </Button>
                </ModalFooter>
            </Modal>
        </React.Fragment>
  );
}

export default Markers;
