FROM python:3.9.5-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev gettext bash

RUN pip install --upgrade pip 

COPY ./requirements.txt /app/requirements.txt
COPY ./entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

RUN pip install -r requirements.txt

COPY . /app/

# create static directory
RUN mkdir static

ENTRYPOINT ["/app/entrypoint.sh"]