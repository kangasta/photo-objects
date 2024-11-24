# Photo Objects

[![CI](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml/badge.svg)](https://github.com/kangasta/photo-objects/actions/workflows/ci.yml)

Application for storing photos in S3 compatible object-storage.

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
