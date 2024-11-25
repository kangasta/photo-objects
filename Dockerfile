FROM python:3.10-slim

WORKDIR /app

COPY manifest.in pyproject.toml requirements.txt ./
RUN pip install -r requirements.txt

COPY back/api/ ./api/
COPY photo_objects/ ./photo_objects/
RUN pip install .
COPY back/entrypoint.sh back/manage.py ./
ENTRYPOINT ["./entrypoint.sh"]
