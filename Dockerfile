FROM python:2.7-slim

RUN export DEBIAN_FRONTEND='noninteractive' && \
    apt-get update -qq && \
    apt-get install -qqy --no-install-recommends git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/*

ADD . /src
WORKDIR /src
RUN pip install -r requirements.txt
CMD python ./bot/app.py
