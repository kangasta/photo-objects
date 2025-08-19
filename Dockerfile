FROM python:3.12-slim AS back

ENV STATIC_ROOT=/app/static/
ENV PHOTO_OBJECTS_HOME=/var/photo_objects/
WORKDIR /app

COPY manifest.in pyproject.toml requirements.txt ./
RUN pip install -r requirements.txt

COPY back/api/ ./api/
COPY photo_objects/ ./photo_objects/
RUN pip install .
COPY back/entrypoint.sh back/gunicorn.conf.py back/manage.py ./
RUN python3 manage.py collectstatic --no-input;
ENTRYPOINT ["./entrypoint.sh"]


FROM nginx:alpine AS front

ENV OBJSTO_HOST=""
ENV OBJSTO_BUCKET=photos
ENV OBJSTO_PROTOCOL=https
ENV OBJSTO_PORT=443

COPY --from=back /app/static /app/static
RUN rm -f /etc/nginx/conf.d/*
COPY front/default.conf.template /etc/nginx/templates/
