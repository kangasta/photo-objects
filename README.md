# Photo Objects

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

<!--
Run unit tests with command:

```bash
python3 -m unittest discover -s tst/
```

Get test coverage with commands:

```bash
coverage run --branch --source yaml_requests/ -m unittest discover -s tst/
coverage report -m
```
-->