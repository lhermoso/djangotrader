#!/usr/bin/env bash
pid=$(ps xa | pgrep -f manage.py\ start_vol)
if [[ -z "$pid" ]]; then
  echo "Starting Volatility Trading"
  /home/leonardo/django-trader/venv/bin/python /home/leonardo/django-trader/manage.py start_vol
fi
