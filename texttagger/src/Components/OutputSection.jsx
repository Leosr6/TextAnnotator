import React, { useState, useEffect } from 'react';
import { Card, CardBody, CardFooter, CardHeader, Button, Popover, PopoverBody, PopoverHeader } from 'reactstrap';
import "./OutputSection.css";
import { Icon } from '@iconify/react';
import arrowBackCircleOutline from '@iconify/icons-ion/arrow-back-circle-outline';
import userIcon from '@iconify/icons-bpmn/user';

const precedence = ["lane", "startevent", "endevent", "xorjoin", "andjoin", "orjoin", "xorsplit", "andsplit", "orsplit",
                    "conditionalintermediateevent", "timerintermediateevent", "messageintermediateevent", "intermediateevent",
                    "task", "activity"]
const stdColor = "black"

function OutputSection(props) {
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [popoverData, setPopoverData] = useState({});
  const [markedText, setMarkedText] = useState([]);
  const {selectedMarkers, metadata, textResources, handleChangeText} = props;

  const handlePopoverShow = (snippet, id) => {

    if (snippet) {
      var popover = {};

      popover.id = id;
      popover.title = snippet.processElementType;
      popover.level = snippet.level;
      popover.lane = snippet.lane;

      setPopoverData(popover);
      setPopoverOpen(true);
    }
  }

  useEffect(() => {
    var text = [];
    var sentences = {};

    if (metadata.text) {
      // Creating an object where the key is the sentenceId for quick access
      for (var sentence of metadata.text.values()) {
        sentences[sentence.sentenceId] = sentence;
      }

      // Adding gateway branches to the snippets
      if (metadata.gateways) {
        for (var gateway of metadata.gateways.values()) {
          for (var branch of gateway.branches.values()) {
            var sentence = sentences[branch.sentenceId];
            var gatewayBranch = Object.assign({isGateway : true}, gateway, branch);

            delete gatewayBranch.branches;
            delete gatewayBranch.sentenceId;

            sentence.snippetList.push(gatewayBranch);
          }
        }
      }

      var sentenceIds = Object.keys(sentences).sort((x, y) => parseInt(x) > parseInt(y));

      for (var sentenceId in sentenceIds) {
        var sentence = sentences[sentenceId];
        var snippetMap = {};

        for (var snippet of sentence.snippetList.values()) {
          var elementType = snippet.processElementType.toLowerCase();
          var markerData = selectedMarkers[elementType];

          if (markerData && markerData.checked) {
            var resource = textResources.find((resource) => snippet.resourceId === resource.id);

            for (var wordIndex = snippet.startIndex -1; wordIndex <= snippet.endIndex -1; wordIndex++) {

              var currentMap = snippetMap[wordIndex];
              if (!currentMap || precedence.indexOf(currentMap.processElementType.toLowerCase()) > precedence.indexOf(elementType)) {
                snippetMap[wordIndex] = {
                  processElementType : snippet.processElementType,
                  resourceId : snippet.resourceId,
                  level : snippet.level,
                  lane : resource ? resource.name : "",
                  icon : wordIndex === snippet.startIndex -1 ? markerData.icon : undefined,
                  marker : snippet.isGateway && wordIndex === snippet.startIndex -1
                };
              }
            }
          }
        }

        var words = sentence.value.split(" ");

        for (var wordIndex = 0; wordIndex < words.length; wordIndex++) {
          var snippet = snippetMap[wordIndex];
          var elementType = snippet && snippet.processElementType.toLowerCase();
          
          if (snippet && snippet.marker && elementType.indexOf("split") !== -1)
            text.push({marker : elementType.replace("split", "branch").toUpperCase()});

          var color = snippet && selectedMarkers[elementType].color;
          text.push({color, word : words[wordIndex], snippet});

          if (snippet && snippet.marker && elementType.indexOf("join") !== -1)
            text.push({marker : elementType.toUpperCase()});
        }
      }
    }

    setMarkedText(text);
  }, [metadata, selectedMarkers, textResources])

  return (
      <Card>
          <CardHeader>Marked Text</CardHeader>
          <CardBody>
            <React.Fragment>
              {markedText.map((wordData, index) =>

                wordData.marker ?
                  <mark key={index}>[{wordData.marker}]</mark>
                  :
                  <React.Fragment key={index}>
                    {wordData.snippet && wordData.snippet.icon &&
                    <Icon icon={wordData.snippet.icon} width="20" height="20" className="mr-2" />
                    }
                    <font id={"word" + index}
                          color={wordData.color || stdColor}
                          onMouseEnter={() => handlePopoverShow(wordData.snippet, "word" + index)}
                          onMouseLeave={() => setPopoverOpen(false)}
                          style={{ fontWeight: wordData.color ? "bold" : "normal" }}>{wordData.word} </font>
                  </React.Fragment>
              )}
              {popoverOpen &&
                <Popover placement="top" isOpen={popoverOpen} target={popoverData.id}>
                  <PopoverHeader>{popoverData.title}</PopoverHeader>
                  <PopoverBody>
                    <Icon icon={userIcon} width="20" height="20" className="mr-2" />
                    <span>{popoverData.lane}</span>
                  </PopoverBody>
                </Popover>
              }
            </React.Fragment>              
          </CardBody>
          <CardFooter>
              <Button outline color="primary" size="sm" onClick={handleChangeText}>
                  <Icon icon={arrowBackCircleOutline} width="20" height="20" className="mr-2" />
                    Change Text
                  </Button>
          </CardFooter>
      </Card>
  );
}

export default OutputSection;
