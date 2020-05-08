import React, { useState } from 'react';
import { Card, CardBody, CardFooter, CardHeader,
          Nav, NavItem, Input, NavLink,
          Button, TabContent, TabPane } from 'reactstrap';
import Dropzone from './Dropzone';
import classnames from 'classnames';

function InputSection(props) {
  const [text, setText] = useState("");
  const [disabledButton, setDisabledButton] = useState(false);
  const [inputTab, setInputTab] = useState("text");
  const [textFile, setTextFile] = useState(null);

  const onClickMarkText = () => {
    var data = new FormData();
    const useFile = inputTab === "1-b";

    if (useFile) {
      if (textFile) {
        data.append('file', textFile);
      }
      else {
        alert("Please select a file or switch to use a text.");
        return;
      }
    }
    else if (text.length === 0) {
      alert("Text can't be empty");
      return;
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
        response.json().then(json => props.handleMarkedText(json))
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
      <Card className="w-75" style={{ height: "85%" }}>
          <CardHeader>Write a process description or upload a text file</CardHeader>
          <CardBody className="ml-3">
              <Nav tabs>
                  <NavItem>
                      <NavLink className={classnames({ active: inputTab === 'text' })} onClick={() => { setInputTab('text'); }}>
                          Text Input
            </NavLink>
                  </NavItem>
                  <NavItem>
                      <NavLink className={classnames({ active: inputTab === 'file' })} onClick={() => { setInputTab('file'); }}>
                          File Input
            </NavLink>
                  </NavItem>
              </Nav>
              <TabContent activeTab={inputTab} style={{ height: "85%", marginTop: "1em" }}>
                  <TabPane tabId="text" className="h-100">
                      <Input type="textarea" className="h-100" id="text" value={text} onChange={(e) => setText(e.target.value)} />
                  </TabPane>
                  <TabPane tabId="file" className="h-100">
                      <Dropzone handleDropAccepted={handleDropAccepted} />
                  </TabPane>
              </TabContent>
          </CardBody>
          <CardFooter className="d-flex">
              <Button color="primary" onClick={onClickMarkText} disabled={disabledButton}>Mark Text</Button>
          </CardFooter>
      </Card>
  );
}

export default InputSection;
