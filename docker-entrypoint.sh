#!/bin/sh

set -e


run_gunicorn(){
	cd app
	exec /usr/bin/gunicorn --config gunicorn.conf.py -b :8000 djangotrader.wsgi
}

run_crond(){
crond -l 2 -f > /dev/stdout 2> /dev/stderr &
}

lets_encrypt(){
  data_path="./nginx/certbot"
  if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi
}

# start cron
lets_encrypt
run_gunicorn
exec "$@"
;;
