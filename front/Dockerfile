FROM nginx:alpine

ENV STATIC_ROOT=""
ENV OBJSTO_BUCKET=photos

RUN rm -f /etc/nginx/conf.d/*
COPY default.conf.template /etc/nginx/templates/
