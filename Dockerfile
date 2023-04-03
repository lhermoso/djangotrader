# syntax=docker/dockerfile:1
FROM python:3.11
LABEL authors="leonardo"

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .
RUN pip install /app/forexconnect-1.6.5.1-cp37-abi3-manylinux1_x86_64.whl
CMD [ "python3", "manage.py" , "run_vol"]