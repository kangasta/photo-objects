from dataclasses import dataclass
from io import StringIO
import os
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import TestCase as DjangoTestCase, override_settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from minio import S3Error

from photo_objects.django import objsto
from photo_objects.django.models import Album, Photo
from photo_objects.django.objsto import _objsto_access


def add_permissions(user, *permissions):
    for permission in permissions:
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='photo_objects',
                codename=permission))


def open_test_photo(filename):
    path = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)),
        "photos",
        filename)
    return open(path, "rb")


def create_dummy_photo(album: Album, filename: str):
    return Photo.objects.create(
        key=f'{album.key}/{filename}',
        album=album,
        timestamp=timezone.now(),
        height=100,
        width=100,)


def _objsto_test_settings():
    return {
        **settings.PHOTO_OBJECTS_OBJSTO,
        "BUCKET": "test-bucket",
        "SECURE": False,
    }


@override_settings(PHOTO_OBJECTS_OBJSTO=_objsto_test_settings())
class TestCase(DjangoTestCase):
    # pylint: disable=invalid-name
    @classmethod
    def tearDownClass(cls):
        client, bucket = _objsto_access()

        for i in client.list_objects(bucket, recursive=True):
            client.remove_object(bucket, i.object_name)

        client.remove_bucket(bucket)

    def assertPhotoInObjsto(self, album_key, photo_key, sizes):
        if not isinstance(sizes, list):
            sizes = [sizes]

        for size in sizes:
            try:
                objsto.get_photo(album_key, photo_key, size)
            except S3Error as e:
                if e.code == "NoSuchKey":
                    raise AssertionError(
                        f"Photo not found: {size}/{album_key}/{photo_key}"
                    ) from None
                else:
                    raise e

    def assertPhotoNotInObjsto(self, album_key, photo_key, sizes):
        if not isinstance(sizes, list):
            sizes = [sizes]

        for size in sizes:
            with self.assertRaises(
                S3Error,
                msg=f"Photo found: {size}/{album_key}/{photo_key}"
            ) as e:
                objsto.get_photo(album_key, photo_key, size)

            self.assertEqual(
                e.exception.code,
                "NoSuchKey",
                f"Photo not found: {size}/{album_key}/{photo_key}")

    def assertTimestampLess(self, a, b, **kwargs):
        '''Assert a is less than b. Automatically parses strings to datetime
        objects.
        '''
        if isinstance(a, str):
            a = parse_datetime(a)
        if isinstance(b, str):
            b = parse_datetime(b)

        return self.assertLess(a, b, **kwargs)

    def assertStatus(self, response, status):
        self.assertEqual(response.status_code, status, response.content)

    def assertRequestStatuses(self, checks):
        for method, path, status in checks:
            with self.subTest(path=path, status=status):
                fn = getattr(self.client, method.lower())
                response = fn(path)
                self.assertStatus(response, status)

    def assertResponseStatusAndItems(self, response, status, expected):
        self.assertStatus(response, status)

        data = response.json()
        for key, expected in expected.items():
            self.assertEqual(data.get(key), expected, f'key={key}')


@dataclass(kw_only=True)
class Timestamps:
    created_at: str = None
    updated_at: str = None


def parse_timestamps(data):
    return Timestamps(
        created_at=data.get('created_at'),
        updated_at=data.get('updated_at'))


# Based on https://stackoverflow.com/a/76745063
def temp_static_files(func):
    '''Decorator that creates a temporary directory, configures that as
    STATIC_ROOT, and collects static files there.'''
    def wrapper(*args, **kwargs):
        static_root = tempfile.mkdtemp(prefix="test_static_")
        with override_settings(STATIC_ROOT=static_root):
            try:
                out = StringIO()
                call_command("collectstatic", "--noinput", stdout=out)
                func(*args, **kwargs)
            finally:
                shutil.rmtree(static_root)

    return wrapper
