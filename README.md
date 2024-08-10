# Photo Objects

[![CI](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml/badge.svg)](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml)

Application for storing photos in S3 compatible object-storage.

## Testing

Check and automatically fix formatting with:

```bash
pycodestyle --exclude api/api/settings.py,*/migrations/*.py api
autopep8 -aaar --in-place api
```

Run static analysis with:

```bash
pylint -E --enable=invalid-name,unused-import,useless-object-inheritance api/api api/photo_objects
```

Run integration tests (in the `api` directory) with:

```bash
cd api
python3 manage.py test
```

Get test coverage with:

```bash
cd api
coverage run --branch --source . manage.py test
coverage report -m
```
