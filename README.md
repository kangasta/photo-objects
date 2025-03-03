# Photo Objects

[![CI](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml/badge.svg)](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml)

Application for storing photos in S3 compatible object-storage.

## Developing

Make migrations:

```sh
python3 back/manage.py makemigrations --pythonpath="$(pwd)"
```

## Testing

Check and automatically fix formatting with:

```sh
pycodestyle --exclude back/api/settings.py,*/migrations/*.py back photo_objects
autopep8 -aaar --in-place --exclude back/api/settings.py,*/migrations/*.py back photo_objects
```

Run static analysis with:

```sh
pylint -E --enable=invalid-name,unused-import,useless-object-inheritance back/api photo_objects
```

Run integration tests (in the `api` directory) with:

```sh
python3 runtests.py
```

Get test coverage with:

```sh
coverage run  --branch --source photo_objects runtests.py
coverage report -m
```
