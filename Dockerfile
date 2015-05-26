FROM alpine

RUN apk add --update \
    python \
    py-pip \
    py-urwid \
    py-twisted && \
rm /var/cache/apk/*

ADD requirements.txt /console/requirements.txt

WORKDIR /console

RUN pip install -r requirements.txt

ADD . /console

RUN python setup.py install

ENTRYPOINT ["docker-console"]
