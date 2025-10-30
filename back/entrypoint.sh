#!/bin/sh -e

# Validate the configuration
python3 manage.py check

# Retry until the database is running
until python3 manage.py migrate 2> /dev/null; do
    sleep 5;
done;

python3 manage.py restore-backup
python3 manage.py create-initial-admin-account
python3 manage.py clean-scaled-photos

exec gunicorn api.wsgi
