from dataclasses import asdict
from io import BytesIO
import json
import mimetypes
import urllib3

from minio import Minio, S3Error

from photo_objects.django.conf import (
    PhotoSize,
    PhotoSizes,
    objsto_settings,
    parse_photo_sizes,
)


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


def _objsto_access() -> tuple[Minio, str]:
    conf = objsto_settings()
    http = urllib3.PoolManager(
        retries=urllib3.util.Retry(connect=1),
        timeout=urllib3.util.Timeout(connect=2.5, read=20),
    )

    client = Minio(
        conf.get('URL'),
        conf.get('ACCESS_KEY'),
        conf.get('SECRET_KEY'),
        http_client=http,
        secure=conf.get('SECURE', True),
    )
    bucket = conf.get('BUCKET', 'photos')

    # TODO: move this to management command
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        client.set_bucket_policy(bucket, _anonymous_readonly_policy(bucket))

    return client, bucket


def photo_path(album_key, photo_key, size_key):
    return f"{size_key}/{album_key}/{photo_key}"


def put_photo(album_key, photo_key, size_key, photo_file):
    content_type = mimetypes.guess_type(photo_key)[0]

    client, bucket = _objsto_access()
    return client.put_object(
        bucket,
        photo_path(album_key, photo_key, size_key),
        photo_file,
        length=-1,
        part_size=10 * MEGABYTE,
        content_type=content_type,
    )


def get_photo(album_key, photo_key, size_key):
    client, bucket = _objsto_access()
    return client.get_object(
        bucket,
        photo_path(album_key, photo_key, size_key)
    )


def delete_photo(album_key, photo_key):
    client, bucket = _objsto_access()

    for i in PhotoSize:
        client.remove_object(bucket, photo_path(album_key, photo_key, i.value))


def delete_scaled_photos(sizes):
    client, bucket = _objsto_access()

    for size in sizes:
        while True:
            objects = client.list_objects(
                bucket,
                prefix=f"{size}/",
                recursive=True)

            if not objects:
                break

            empty = True
            for i in objects:
                empty = False
                client.remove_object(bucket, i.object_name)
                yield i.object_name

            if empty:
                break


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
    data = json.dumps(asdict(sizes))
    stream = BytesIO(data.encode('utf-8'))

    client, bucket = _objsto_access()
    client.put_object(
        bucket,
        "photo_sizes.json",
        stream,
        length=-1,
        part_size=10 * MEGABYTE,
        content_type="application/json",
    )


def get_photo_sizes() -> PhotoSizes:
    client, bucket = _objsto_access()
    try:
        data = client.get_object(bucket, "photo_sizes.json")
        return parse_photo_sizes(json.loads(data.read()))
    except S3Error as e:
        if e.code == "NoSuchKey":
            return None
        raise
