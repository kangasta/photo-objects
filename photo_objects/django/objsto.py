import json
import mimetypes
import urllib3

from django.conf import settings

from minio import Minio


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
    conf = settings.PHOTO_OBJECTS_OBJSTO

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
    return f"{album_key}/{photo_key}/{size_key}"


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

    for i in client.list_objects(
            bucket,
            prefix=photo_path(
                album_key,
                photo_key,
                ""),
            recursive=True):
        client.remove_object(bucket, i.object_name)
