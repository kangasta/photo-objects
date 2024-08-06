import os

from minio import Minio


MEGABYTE = 1 << 20


def _objsto_access() -> tuple[Minio, str]:
    client = Minio(
        os.getenv('OBJSTO_URL', "localhost:9000"),
        os.getenv('OBJSTO_ACCESS_KEY', "access_key"),
        os.getenv('OBJSTO_SECRET_KEY', "secret_key"),
        secure=os.getenv('OBJSTO_SECURE', "false").lower() == "true",
    )
    bucket = os.getenv('OBJSTO_BUCKET', "photos")

    # TODO: move this to management command
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    return client, bucket


def photo_path(album_key, photo_key, size_key):
    return f"{album_key}/{size_key}/{photo_key}"


def put_photo(album_key, photo_key, size_key, photo_file):
    client, bucket = _objsto_access()
    return client.put_object(bucket, photo_path(album_key, photo_key, size_key), photo_file, length=-1, part_size=10*MEGABYTE)


def get_photo(album_key, photo_key, size_key):
    client, bucket = _objsto_access()
    return client.get_object(bucket, photo_path(album_key, photo_key, size_key))
