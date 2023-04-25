FROM debian:buster
WORKDIR /app
EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt install -y git python3 python3-pip cron

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

RUN crontab -l | { cat; echo "*/15 * * * 0-5 python /app/manage.py optimize_vol"; } | crontab -
COPY . .
CMD cron
CMD [ "python3","-i","manage.py" , "start_vol"]