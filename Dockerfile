FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -yqq \
    python3-pip \
    python3-tk \
    git \
    iproute2 \
    libpq-dev \
    python3-pyqt5.qtopengl \
    python3-pyqt5.qtwebkit

ADD ./scripts/99-serial.rules /etc/udev/rules.d/

RUN pip install -U pip
RUN pip install pyqt5 jupyter psycopg2 flake8 pgcopy pyserial pytest

EXPOSE $TIMESCALE_DB_PORT