FROM python:3.9.5-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev gettext bash

RUN pip install --upgrade pip 

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

COPY . /app/

EXPOSE 8000
CMD ["gunicorn","--bind", ":8000", "config.wsgi:application"]