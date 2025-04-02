#!/bin/sh

echo "Waiting for the admin user to be created..."
until test -f /var/photo_objects/initial_admin_password; do
  sleep 3;
done

echo "USERNAME: admin" > .env
echo "PASSWORD: $(cat /var/photo_objects/initial_admin_password)" >> .env

echo "Waiting for the server to be ready..."
url="${BASE_URL:-http://localhost:8080}"
until curl -sf $url; do
  sleep 3;
done

exec npx playwright test
