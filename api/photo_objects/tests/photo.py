import datetime
import json
import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from photo_objects.models import Album, Photo
from photo_objects.object_storage import get_photo, _objsto_access


def _open_test_photo(filename):
    path = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)),
        "photos",
        filename)
    return open(path, "rb")


class PhotoViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(username='no_permission', password='test')

        has_permission = User.objects.create_user(
            username='has_permission', password='test')
        has_permission.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='photo_objects',
                codename='add_photo'))
        has_permission.user_permissions.add(
            Permission.objects.get(
                content_type__app_label='photo_objects',
                codename='change_album'))

        Album.objects.create(key="test", visibility=Album.Visibility.PUBLIC)

    @classmethod
    def tearDownClass(_):
        client, bucket = _objsto_access()

        for i in client.list_objects(bucket, recursive=True):
            client.remove_object(bucket, i.object_name)

        client.remove_bucket(bucket)

    def test_post_photo_with_non_formdata_fails(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        data = self.client.post(
            "/api/albums/test/photos",
            "key=venice",
            content_type="text/plain")
        self.assertEqual(data.status_code, 415, json.dumps(data.json()))

    def test_post_photo_without_files_fails(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        data = self.client.post(
            "/api/albums/test/photos",)
        self.assertEqual(data.status_code, 400, json.dumps(data.json()))

    def test_put_photo_fails(self):
        data = self.client.put("/api/albums/test/photos")
        self.assertEqual(data.status_code, 405, json.dumps(data.json()))

    def test_cannot_upload_photo_without_permission(self):
        data = self.client.post("/api/albums/test/photos")
        self.assertEqual(data.status_code, 401, json.dumps(data.json()))

        login_success = self.client.login(
            username='no_permission', password='test')
        self.assertTrue(login_success)

        data = self.client.post("/api/albums/test/photos")
        self.assertEqual(data.status_code, 403, json.dumps(data.json()))

    def test_upload_photo(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        filename = "tower.jpg"
        file = _open_test_photo(filename)
        data = self.client.post(
            "/api/albums/test/photos",
            {filename: file})
        self.assertEqual(data.status_code, 201, json.dumps(data.json()))

        photo = Photo.objects.get(key=filename)
        self.assertEqual(photo.timestamp, timezone.datetime(
            2024, 3, 20, 14, 28, 4, 0, datetime.timezone.utc))

        file.seek(0)
        photo_response = get_photo("test", filename, "og")
        self.assertEqual(
            photo_response.read(),
            file.read(),
            "Photo in the file system does not match photo uploaded to the object storage")  # noqa

        file.seek(0)
        data = self.client.post(
            "/api/albums/test/photos",
            {filename: file})
        self.assertEqual(data.status_code, 409, json.dumps(data.json()))

    def test_create_photo_key_validation(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        file = _open_test_photo("tower.jpg")
        data = self.client.post(
            "/api/albums/test/photos",
            {"": file})
        self.assertEqual(data.status_code, 400, json.dumps(data.json()))
