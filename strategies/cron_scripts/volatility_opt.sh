#!/usr/bin/env bash
pid=$(ps xa | pgrep -f manage.py\ optimize_vol)
if [[ -z "$pid" ]]; then
  echo "Starting Volatility Optimization"
  /home/leonardo/django-trader/venv/bin/python /home/leonardo/django-trader/manage.py optimize_vol
fi
