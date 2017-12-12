FROM python:3.6.3-slim

RUN apt-get update --no-install-recommends && \
    apt-get install -y supervisor

WORKDIR /code
ADD requirements.txt /code/requirements.txt
RUN pip install -r requirements.txt

COPY db /code/db
COPY utils.py /code/utils.py
COPY collectAgent.py /code/collectAgent.py
COPY collectServer.py /code/collectServer.py
COPY websock.py /code/websock.py
COPY settings.yaml /code/settings.yaml


