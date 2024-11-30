# Photo Objects

[![CI](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml/badge.svg)](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml)

Application for storing photos in S3 compatible object-storage.

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

Check and automatically fix formatting with:

```bash
pycodestyle --exclude back/api/settings.py,*/migrations/*.py back photo_objects
autopep8 -aaar --in-place --exclude back/api/settings.py,*/migrations/*.py back photo_objects
```

Run static analysis with:

```bash
pylint -E --enable=invalid-name,unused-import,useless-object-inheritance back/api photo_objects
```

Run integration tests (in the `api` directory) with:

```bash
python3 runtests.py
```

Get test coverage with:

```bash
coverage run  --branch --source photo_objects runtests.py
coverage report -m
```
