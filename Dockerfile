FROM debian:bookworm-slim as web
LABEL maintainer="Leo Hermoso <leo@leohermoso.com.br>"

WORKDIR /
EXPOSE 8000


ENV PATH="/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#Setup Inicial
RUN mkdir -p DjangoTrader
COPY ./app /DjangoTrader/app/
COPY ./docker-entrypoint.sh /DjangoTrader/


RUN chmod +x /DjangoTrader/docker-entrypoint.sh

WORKDIR /DjangoTrader



RUN apt-get update && apt install -y git pkg-config python3 python3-pip cron mariadb-client libmariadb-dev python3-dev curl python3-gunicorn gunicorn python3-dev default-libmysqlclient-dev build-essential

RUN pip install -r app/requirements.txt --break-system-packages
RUN pip install python-dotenv --break-system-packages


