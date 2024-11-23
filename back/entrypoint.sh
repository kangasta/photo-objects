#!/bin/sh

# Validate the configuration
python3 manage.py check

# Retry until the database is running
until python3 manage.py migrate 2> /dev/null; do
    sleep 5;
done;

python3 manage.py create-initial-admin-account

if [ -n "$STATIC_ROOT" ]; then
    python3 manage.py collectstatic --no-input;
fi

exec gunicorn -w 8 -b 0.0.0.0:8000 api.wsgi
