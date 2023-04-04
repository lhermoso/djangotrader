# syntax=docker/dockerfile:1
FROM python:3.7-alpine
LABEL authors="leonardo"

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .
#RUN pip install forexconnect
CMD [ "python3", "manage.py" , "run_vol","&"]