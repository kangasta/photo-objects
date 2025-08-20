from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from minio import S3Error

from photo_objects.django import objsto
from photo_objects.django.conf import CONFIGURABLE_PHOTO_SIZES
from photo_objects.django.models import Album

from .utils import TestCase, open_test_photo


class PhotoViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(
            username='superuser',
            password='test',
            is_staff=True,
            is_superuser=True)

        Album.objects.create(
            key="test-photo-sizes",
            visibility=Album.Visibility.PUBLIC)

    def _scale_image(self, album_key, photo_key):
        for size in CONFIGURABLE_PHOTO_SIZES:
            response = self.client.get(
                f"/api/albums/{album_key}/photos/{photo_key}/img?size={size}")
            self.assertStatus(response, 200)

    def assertPhotoFound(self, album_key, photo_key, sizes):
        if not isinstance(sizes, list):
            sizes = [sizes]

        for size in sizes:
            try:
                objsto.get_photo(album_key, photo_key, size)
            except S3Error as e:
                if e.code == "NoSuchKey":
                    raise AssertionError(
                        f"Photo not found: {size}/{album_key}/{photo_key}")
                else:
                    raise e

    def assertPhotoNotFound(self, album_key, photo_key, sizes):
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

    def test_clean_scaled_photos(self):
        login_success = self.client.login(
            username='superuser', password='test')
        self.assertTrue(login_success)

        filename = "tower.jpg"
        file = open_test_photo(filename)
        response = self.client.post(
            "/api/albums/test-photo-sizes/photos",
            {filename: file})
        self.assertStatus(response, 201)

        self._scale_image("test-photo-sizes", "tower.jpg")
        self.assertPhotoFound("test-photo-sizes",
                              "tower.jpg", ["sm", "md", "lg", "og"])

        out = StringIO()
        call_command('clean-scaled-photos', stdout=out)
        output = out.getvalue()
        self.assertIn("No previous photo sizes configuration found", output)
        self.assertIn("Total deleted photos: 3", output)
        self.assertPhotoNotFound(
            "test-photo-sizes",
            "tower.jpg",
            CONFIGURABLE_PHOTO_SIZES)
        self.assertPhotoFound("test-photo-sizes", "tower.jpg", "og")

        self._scale_image("test-photo-sizes", "tower.jpg")
        self.assertPhotoFound("test-photo-sizes",
                              "tower.jpg", ["sm", "md", "lg", "og"])

        with self.settings(PHOTO_OBJECTS_PHOTO_SIZES=dict(
            sm=dict(max_width=256, max_height=256),
        )):
            out = StringIO()
            call_command('clean-scaled-photos', stdout=out)
            output = out.getvalue()
            self.assertIn(
                "Found changes in photo sizes configuration for sm sizes.",
                output)
            self.assertIn("Total deleted photos: 1", output)
            self.assertPhotoNotFound("test-photo-sizes", "tower.jpg", "sm")
            self.assertPhotoFound("test-photo-sizes",
                                  "tower.jpg", ["md", "lg", "og"])

        response = self.client.delete(
            "/api/albums/test-photo-sizes/photos/tower.jpg")
        self.assertStatus(response, 204)
        self.assertPhotoNotFound(
            "test-photo-sizes", "tower.jpg", ["sm", "md", "lg", "og"])
