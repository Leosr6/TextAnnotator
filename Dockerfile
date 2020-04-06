FROM ubuntu:16.04

LABEL maintainer="leosrosa96@gmail.com"

RUN apt-get update -y && \
    apt-get install default-jre -y && \
    apt-get install python3 -y && \
    apt-get install python3-pip -y

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /backend/requirements.txt

WORKDIR /

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r /backend/requirements.txt

COPY . /backend

CMD [ "python3", "/backend/src/TextReaderService.py" ]