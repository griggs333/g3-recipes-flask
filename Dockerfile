FROM python:3.10-slim-buster

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app

ENV PORT 8080

CMD gunicorn -c gunicorn_conf.py app:app