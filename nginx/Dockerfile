FROM nginx

RUN rm /etc/nginx/conf.d/default.conf && touch /etc/nginx/conf.d/default.conf
COPY lemon.army /etc/letsencrypt/live/
COPY djangotrader.conf.template /etc/nginx/templates/