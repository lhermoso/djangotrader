FROM nginx

RUN rm /etc/nginx/conf.d/default.conf && touch /etc/nginx/conf.d/default.conf
# COPY musclewiki.conf /etc/nginx/conf.d/
COPY lemon.army /etc/letsencrypt/live/
COPY musclewiki.conf.template /etc/nginx/templates/