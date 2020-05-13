import React, { useState, useEffect } from 'react';
import { Card, CardBody, CardFooter, CardHeader, Button, Popover, PopoverBody, PopoverHeader, CustomInput } from 'reactstrap';
import "./OutputSection.css";
import { Icon } from '@iconify/react';
import arrowBackCircleOutline from '@iconify/icons-ion/arrow-back-circle-outline';
import userIcon from '@iconify/icons-bpmn/user';

const precedence = ["lane", "startevent", "endevent", "xorjoin", "andjoin", "orjoin", "xorsplit", "andsplit", "orsplit",
                    "conditionalintermediateevent", "timerintermediateevent", "messageintermediateevent", "intermediateevent", "task"]
const stdColor = "black"

function OutputSection(props) {
  const [popoverOpen, setPopoverOpen] = useState(false);
  const [popoverData, setPopoverData] = useState({});
  const [markedText, setMarkedText] = useState([]);
  const [showIcons, setShowIcons] = useState(true);
  const {selectedMarkers, metadata, textResources, handleChangeText} = props;

  const handlePopoverShow = (snippet, id) => {
    if (snippet) {
      var popover = {};

      popover.id = id;
      popover.title = snippet.marker;
      popover.level = snippet.level;
      popover.lane = snippet.lane;
      popover.icon = snippet.icon;

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
          for (var branchIndex in gateway.branches) {
            var branch = gateway.branches[branchIndex];
            var sentence = sentences[branch.sentenceId];
            var gatewayBranch = Object.assign({isBranch : true, hideIcon : branchIndex > 0}, gateway, branch);

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
        var markerMap = {};

        for (var snippet of sentence.snippetList.values()) {
          var elementType = snippet.processElementType.toLowerCase();
          var markerData = selectedMarkers[elementType];

          if (markerData && markerData.checked) {
            var resource = textResources.find((resource) => snippet.resourceId === resource.id);

            for (var wordIndex = snippet.startIndex; wordIndex <= snippet.endIndex; wordIndex++) {
              var currentMap = snippetMap[wordIndex];

              if (!currentMap || precedence.indexOf(currentMap.processElementType) >= precedence.indexOf(elementType)) {
                if (!snippet.isBranch || snippet.isExplicit) {
                  snippetMap[wordIndex] = {
                    marker : markerData.marker,
                    processElementType : elementType,
                    resourceId : snippet.resourceId,
                    level : snippet.level,
                    lane : resource ? resource.name : ""
                  };
                }
                if (wordIndex === snippet.startIndex && !snippet.isBranch && snippetMap[wordIndex]) {
                  snippetMap[wordIndex].icon = markerData.icon;
                }
              }

              if (wordIndex === snippet.startIndex && snippet.isBranch) {
                markerMap[wordIndex] = {
                  text : elementType.replace("split", "branch").toUpperCase(),
                  icon : !snippet.hideIcon ? markerData.icon : null
                };
              }
            }
          }
        }

        var words = sentence.value.split(" ");

        for (var wordIndex = 0; wordIndex < words.length; wordIndex++) {          
          var snippet = snippetMap[wordIndex];
          var marker = markerMap[wordIndex];

          if (marker) {
            if (marker.icon)
              text.push({icon : marker.icon});
            text.push({marker : marker.text});
          }

          var color = null;

          if (snippet) {
            var elementType = snippet.processElementType;
            color = selectedMarkers[elementType].color;
            if (snippet.icon)
              text.push({icon : snippet.icon});
          }

          text.push({color, word : words[wordIndex], snippet});
        }
      }
    }

    setMarkedText(text);
  }, [metadata, selectedMarkers, textResources])

  return (
      <Card className="mb-5">
          <CardHeader>
            <div className="d-flex">
              Marked Text
              <CustomInput type="switch" label="Show icons" id="iconsOnText" checked={showIcons} onChange={(e) => setShowIcons(e.target.checked)} className="ml-auto" />
            </div>
          </CardHeader>
          <CardBody>
            <React.Fragment>
              {markedText.map((wordData, index) =>
                <React.Fragment key={index}>
                {wordData.marker &&
                  <mark key={index}>[{wordData.marker}]</mark>
                }
                {wordData.icon && showIcons &&
                  <Icon icon={wordData.icon} width="20" height="20" className="mr-2" />
                }
                {wordData.word &&
                    <font id={"word" + index}
                          color={wordData.color || stdColor}
                          onMouseEnter={() => handlePopoverShow(wordData.snippet, "word" + index)}
                          onMouseLeave={() => setPopoverOpen(false)}
                          style={{ fontWeight: wordData.color ? "bold" : "normal" }}>{wordData.word} </font>
                }
                </React.Fragment>
              )}
              {popoverOpen &&
                <Popover placement="top" isOpen={popoverOpen} target={popoverData.id}>
                  <PopoverHeader>
                    <Icon icon={popoverData.icon} width="20" height="20" className="mr-2" />
                    {popoverData.title}
                  </PopoverHeader>
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
