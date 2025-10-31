from dataclasses import asdict
from io import BytesIO
import json
import mimetypes
import re
import urllib3

from minio import Minio, S3Error

from photo_objects.django.conf import (
    PhotoSize,
    PhotoSizes,
    objsto_settings,
    parse_photo_sizes,
)
from photo_objects.utils import slugify


MEGABYTE = 1 << 20


def _anonymous_readonly_policy(bucket: str):
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket}/*",
            },
        ],
    }
    return json.dumps(policy)


def _objsto_access() -> tuple[dict, Minio]:
    conf = objsto_settings()
    http = urllib3.PoolManager(
        retries=urllib3.util.Retry(connect=1),
        timeout=urllib3.util.Timeout(connect=2.5, read=20),
    )

    return (conf, Minio(
        conf.get('URL'),
        conf.get('ACCESS_KEY'),
        conf.get('SECRET_KEY'),
        http_client=http,
        secure=conf.get('SECURE', True),
    ))


def _backup_access() -> tuple[Minio, str]:
    conf, client = _objsto_access()
    bucket = conf.get('BACKUP_BUCKET', 'backups')

    # TODO: move this to management command
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    return client, bucket


def _photos_access() -> tuple[Minio, str]:
    conf, client = _objsto_access()
    bucket = conf.get('BUCKET', 'photos')

    # TODO: move this to management command
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        client.set_bucket_policy(bucket, _anonymous_readonly_policy(bucket))

    return client, bucket


def _put_json(key, data, access_fn):
    data_str = json.dumps(data)
    stream = BytesIO(data_str.encode('utf-8'))

    client, bucket = access_fn()
    client.put_object(
        bucket,
        key,
        stream,
        length=-1,
        part_size=10 * MEGABYTE,
        content_type="application/json",
    )


def _list_all(client: Minio, bucket: str, prefix: str):
    start_after = None
    while True:
        objects = client.list_objects(
            bucket,
            prefix=prefix,
            recursive=True,
            start_after=start_after)

        if not objects:
            break

        empty = True
        for i in objects:
            empty = False
            yield i
            start_after = i.object_name

        if empty:
            break


def _get_all(client: Minio, bucket: str, prefix: str):
    for i in _list_all(client, bucket, prefix):
        yield client.get_object(bucket, i.object_name)


def _delete_all(client: Minio, bucket: str, prefix: str):
    for i in _list_all(client, bucket, prefix):
        client.remove_object(bucket, i.object_name)
        yield i.object_name


def backup_info_key(id_):
    return f'info_{id_}.json'


def backup_data_key(id_, type_, key):
    return f'data_{id_}/{type_}_{slugify(key)}.json'


def backup_data_prefix(id_, type_=None):
    return f'data_{id_}/{type_ or ""}'


def put_backup_json(key: str, data: dict):
    return _put_json(key, data, _backup_access)


def get_backup_object(backup_id: int):
    client, bucket = _backup_access()

    try:
        data = client.get_object(bucket, backup_info_key(backup_id))
        return json.loads(data.read())
    except S3Error as e:
        if e.code == "NoSuchKey":
            return None
        raise


def get_backup_objects():
    client, bucket = _backup_access()
    return [json.loads(i.read()) for i in _get_all(client, bucket, 'info_')]


def get_backup_data(id_: int, type_=None):
    client, bucket = _backup_access()
    for i in _get_all(client, bucket, backup_data_prefix(id_, type_)):
        yield json.loads(i.read())


def delete_backup_objects(id_: int):
    client, bucket = _backup_access()
    client.remove_object(bucket, backup_info_key(id_))
    for _ in _delete_all(client, bucket, backup_data_prefix(id_)):
        continue


def photo_path(album_key, photo_key, size_key):
    return f"{size_key}/{album_key}/{photo_key}"


def _photo_filename(photo_key: str, image_format: str = None) -> str:
    if image_format:
        filename = re.sub(r'\.[^.]+$', '', photo_key)
        return f"{filename}.{image_format.lower()}"

    return photo_key


def photo_content_headers(
    photo_key: str,
    image_format: str = None,
) -> tuple[str, dict[str, str]]:
    filename = _photo_filename(photo_key, image_format)

    content_type = mimetypes.guess_type(filename, strict=False)[0]
    headers = {
        "Content-Disposition": f"inline; filename={filename}"
    }

    return content_type, headers


def put_photo(album_key, photo_key, size_key, photo_file, image_format=None):
    content_type, headers = photo_content_headers(photo_key, image_format)

    client, bucket = _photos_access()
    return client.put_object(
        bucket,
        photo_path(album_key, photo_key, size_key),
        photo_file,
        length=-1,
        part_size=10 * MEGABYTE,
        content_type=content_type,
        metadata=headers
    )


def get_photo(album_key, photo_key, size_key):
    client, bucket = _photos_access()
    return client.get_object(
        bucket,
        photo_path(album_key, photo_key, size_key)
    )


def delete_photo(album_key, photo_key):
    client, bucket = _photos_access()

    for i in PhotoSize:
        client.remove_object(bucket, photo_path(album_key, photo_key, i.value))


def delete_scaled_photos(sizes):
    client, bucket = _photos_access()

    for size in sizes:
        yield from _delete_all(client, bucket, f'{size}/')


def get_error_code(e: Exception) -> str:
    try:
        return e.code
    except AttributeError:
        return None


def with_error_code(msg: str, e: Exception) -> str:
    code = get_error_code(e)
    if code:
        return f'{msg} ({code})'
    return msg


def put_photo_sizes(sizes: PhotoSizes):
    return _put_json("photo_sizes.json", asdict(sizes), _photos_access)


def get_photo_sizes() -> PhotoSizes:
    client, bucket = _photos_access()
    try:
        data = client.get_object(bucket, "photo_sizes.json")
        return parse_photo_sizes(json.loads(data.read()))
    except S3Error as e:
        if e.code == "NoSuchKey":
            return None
        raise
