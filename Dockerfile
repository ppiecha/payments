# pull official base image
FROM python:3.8.12-alpine

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk add build-base

# copy requirements file
COPY requirements.txt requirements.txt

# install dependencies
RUN pip install -r requirements.txt

# copy project
COPY . .