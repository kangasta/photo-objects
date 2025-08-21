from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command

from photo_objects.django.conf import CONFIGURABLE_PHOTO_SIZES
from photo_objects.django.models import Album

from .utils import TestCase, open_test_photo


class PhotoViewTests(TestCase):
    def setUp(self):
        user = get_user_model()
        user.objects.create_user(
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
        self.assertPhotoInObjsto(
            "test-photo-sizes", "tower.jpg", ["sm", "md", "lg", "og"])

        out = StringIO()
        call_command('clean-scaled-photos', stdout=out)
        output = out.getvalue()
        self.assertIn("No previous photo sizes configuration found", output)
        self.assertIn("Total deleted photos: 3", output)
        self.assertPhotoNotInObjsto(
            "test-photo-sizes",
            "tower.jpg",
            CONFIGURABLE_PHOTO_SIZES)
        self.assertPhotoInObjsto("test-photo-sizes", "tower.jpg", "og")

        self._scale_image("test-photo-sizes", "tower.jpg")
        self.assertPhotoInObjsto(
            "test-photo-sizes", "tower.jpg", ["sm", "md", "lg", "og"])

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
            self.assertPhotoNotInObjsto("test-photo-sizes", "tower.jpg", "sm")
            self.assertPhotoInObjsto(
                "test-photo-sizes", "tower.jpg", ["md", "lg", "og"])

        response = self.client.delete(
            "/api/albums/test-photo-sizes/photos/tower.jpg")
        self.assertStatus(response, 204)
        self.assertPhotoNotInObjsto(
            "test-photo-sizes", "tower.jpg", ["sm", "md", "lg", "og"])
