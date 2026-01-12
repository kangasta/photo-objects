# Photo Objects

[![CI](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml/badge.svg)](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml)
[![Release](https://github.com/kangasta/photo-objects/actions/workflows/release.yml/badge.svg)](https://github.com/kangasta/photo-objects/actions/workflows/release.yml)

Application for storing photos in S3 compatible object-storage. Key features:

- Automatically scales photos according to different sizes defined in settings.
- Provides simple grouping and access control for the photos with albums.

## Developing

Build containers:

```sh
docker compose build
```

Start or update development environment:

```sh
docker compose up -d
```

Print initial admin password (username of the initial administrator account is `admin`):

```sh
docker compose exec api cat /var/photo_objects/initial_admin_password
```

Make database migrations (requires development environment to be running):

```sh
python3 back/manage.py makemigrations --pythonpath="$(pwd)"
```

## Getting started

Run the application in a Docker Compose configuration with `docker compose up -d`.

```sh
docker compose up -d
```

Use initial admin credentials to login to the application. The username is admin and the initial admin password is available in the api containers logs and in /var/photo_objects/initial_admin_password file. Easiest way to see the password is to run `docker compose exec api cat /var/photo_objects/initial_admin_password`.

```sh
docker compose exec api cat /var/photo_objects/initial_admin_password
```

The configuration includes an init container, `demo`, that uploads demo content to the application. To remove the demo content, run the demo container with clean argument:

```sh
docker compose run demo clean
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
