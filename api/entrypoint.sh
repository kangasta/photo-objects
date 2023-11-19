#!/bin/sh

# Retry until the database is running
until python3 manage.py migrate 2> /dev/null; do
    sleep 5;
done;

python3 manage.py create-initial-admin-account

# TODO: replace with gunicorn server
exec python3 manage.py runserver 0.0.0.0:8000
