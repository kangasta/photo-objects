FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY api/ ./api/
COPY photo_objects/ ./photo_objects/
COPY entrypoint.sh manage.py ./
ENTRYPOINT ["./entrypoint.sh"]
