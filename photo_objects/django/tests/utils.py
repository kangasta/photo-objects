from dataclasses import dataclass
import os

from django.conf import settings
from django.test import TestCase as DjangoTestCase, override_settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from photo_objects.django.models import Album, Photo
from photo_objects.django.objsto import _objsto_access


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
    @classmethod
    def tearDownClass(_):
        client, bucket = _objsto_access()

        for i in client.list_objects(bucket, recursive=True):
            client.remove_object(bucket, i.object_name)

        client.remove_bucket(bucket)

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
