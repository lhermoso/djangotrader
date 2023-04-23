# syntax=docker/dockerfile:1
LABEL authors="leonardo"
FROM debian:buster
WORKDIR /app
EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt install -y git python3 python3-pip cron python-certbot-nginx

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

RUN crontab -l | { cat; echo "*/15 * * * 0-5 python /app/manage.py run_vol_opt"; } | crontab -
COPY . .
CMD cron
CMD [ "python3", "manage.py" , "run_vol"]