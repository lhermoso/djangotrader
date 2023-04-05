# syntax=docker/dockerfile:1
FROM python:3.7.16
LABEL authors="leonardo"
#RUN apt-get update && apt install -y git python3 python3-pip

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .
#RUN pip install forexconnect

CMD [ "python3", "manage.py" , "run_vol"]