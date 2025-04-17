FROM python:3.10-slim as back

ENV PHOTO_OBJECTS_HOME=/var/photo_objects/
WORKDIR /app

COPY manifest.in pyproject.toml requirements.txt ./
RUN pip install -r requirements.txt

COPY back/api/ ./api/
COPY photo_objects/ ./photo_objects/
RUN pip install .
COPY back/entrypoint.sh back/gunicorn.conf.py back/manage.py ./
ENTRYPOINT ["./entrypoint.sh"]

FROM back as static

ENV STATIC_ROOT=/app/static/
RUN python3 manage.py collectstatic --no-input;

FROM nginx:alpine as front

ENV OBJSTO_URL=""
ENV OBJSTO_BUCKET=photos

COPY --from=static /app/static /app/static
RUN rm -f /etc/nginx/conf.d/*
COPY front/default.conf.template /etc/nginx/templates/
