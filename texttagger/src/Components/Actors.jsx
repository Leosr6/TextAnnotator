import React from 'react';
import { Card, CardBody, CardHeader} from 'reactstrap';
import { Icon } from '@iconify/react';
import userIcon from '@iconify/icons-bpmn/user';

function Actors(props) {
    return (
        <Card className="mt-3">
            <CardHeader>
                <div className="d-flex">
                    Actors
                </div>
            </CardHeader>
            <CardBody>
                {props.textResources.map((resource, index) =>
                    <div className="d-flex align-items-center" key={index}>
                        <Icon icon={userIcon} width="20" height="20" className="mr-2" />
                        <span>{resource.name}</span>
                    </div>
                )}
            </CardBody>
        </Card>
    );
}

export default Actors;
