import React, {useMemo} from 'react';
import {useDropzone} from 'react-dropzone';

const baseStyle = {
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  padding: '20px',
  borderWidth: 2,
  borderRadius: 2,
  borderColor: '#eeeeee',
  borderStyle: 'dashed',
  backgroundColor: '#fafafa',
  color: '#787878',
  outline: 'none',
  transition: 'border .24s ease-in-out',
  height: '100%'
};

const activeStyle = {
  borderColor: '#2196f3'
};

const acceptStyle = {
  borderColor: '#00e676'
};

const rejectStyle = {
  borderColor: '#ff1744'
};

function Dropzone(props) {
  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragAccept,
    isDragReject,
    acceptedFiles
  } = useDropzone({accept: 'text/plain', multiple: false, onDropAccepted: props.handleDropAccepted});

  const style = useMemo(() => ({
    ...baseStyle,
    ...(isDragActive ? activeStyle : {}),
    ...(isDragAccept ? acceptStyle : {}),
    ...(isDragReject ? rejectStyle : {})
  }), [
    isDragActive,
    isDragAccept,
    isDragReject
  ]);

  return (
    <div style={{height: "80%"}}>
      <div {...getRootProps({style})}>
        <input {...getInputProps()} />
        <p>Drag and drop a file, or click to select one</p>
      </div>
      <aside className="mt-2">
        {acceptedFiles.length > 0 &&
          <p>{acceptedFiles[0].name} - {acceptedFiles[0].size} bytes</p>
        }
      </aside>
    </div>
  );
}

export default Dropzone;