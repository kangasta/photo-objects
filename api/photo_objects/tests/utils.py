import os

from django.conf import settings
from django.test import TestCase as DjangoTestCase, override_settings

from photo_objects.objsto import _objsto_access


def open_test_photo(filename):
    path = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)),
        "photos",
        filename)
    return open(path, "rb")


def _objsto_test_settings():
    return {
        **settings.PHOTO_OBJECTS_OBJSTO,
        "BUCKET": "test-bucket",
    }


@override_settings(PHOTO_OBJECTS_OBJSTO=_objsto_test_settings())
class TestCase(DjangoTestCase):
    @classmethod
    def tearDownClass(_):
        client, bucket = _objsto_access()

        for i in client.list_objects(bucket, recursive=True):
            client.remove_object(bucket, i.object_name)

        client.remove_bucket(bucket)

    def assertStatus(self, response, status):
        self.assertEqual(response.status_code, status, response.content)

    def assertRequestStatuses(self, checks):
        for method, path, status in checks:
            with self.subTest(path=path, status=status):
                fn = getattr(self.client, method.lower())
                response = fn(path)
                self.assertStatus(response, status)
