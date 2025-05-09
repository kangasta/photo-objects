#!/bin/sh

# Validate the configuration
python3 manage.py check

# Retry until the database is running
until python3 manage.py migrate 2> /dev/null; do
    sleep 5;
done;

python3 manage.py create-initial-admin-account
python3 manage.py create-site-albums

exec gunicorn api.wsgi
