FROM python:3
ENV PYTHONUNBUFFERED 1
ENV RUNNING_IN_DOCKER 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
RUN apt update && apt install postgresql-client -y