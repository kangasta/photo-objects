# Photo Objects

[![CI](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml/badge.svg)](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml)

Application for storing photos in S3 compatible object-storage.

## Developing

Make migrations:

```sh
python3 back/manage.py makemigrations --pythonpath="$(pwd)"
```

## Testing

### Static analysis

Check and automatically fix formatting with:

```sh
pycodestyle --exclude back/api/settings.py,*/migrations/*.py back photo_objects
autopep8 -aaar --in-place --exclude back/api/settings.py,*/migrations/*.py back photo_objects
```

Run static analysis with:

```sh
pylint back/api photo_objects
```

### Integration tests

Run integration tests (in the `api` directory) with:

```sh
python3 runtests.py
```

Get test coverage with:

```sh
coverage run --branch --source photo_objects runtests.py
coverage report -m
```

### End-to-end tests

Run end-to-end tests with Docker Compose:

```sh
docker compose -f docker-compose.test.yaml up --exit-code-from test --build
```

Run end-to-end tests in interactive mode (in the `tests` directory):

```sh
# Install dependencies
npm ci

# Start test target
docker compose up -d

# Configure credentials
export USERNAME=admin
export PASSWORD=$(docker compose exec api cat /var/photo_objects/initial_admin_password)

# Start test UI
npx playwright test --ui
```
