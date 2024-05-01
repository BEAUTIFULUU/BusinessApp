FROM python:3.11.4-slim-buster

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y libmagic-dev python3-dev default-libmysqlclient-dev build-essential pkg-config

COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .



