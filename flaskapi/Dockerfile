FROM python:3.8-slim-buster
WORKDIR /flaskapi
COPY ./requirements.txt /flaskapi/requirements.txt
RUN pip install -r requirements.txt
COPY . /flaskapi
