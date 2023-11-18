from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Album, Photo


class AuthViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(username='test', password='test')

        public_album = Album.objects.create(key="venice", public=True)
        public_photo = Photo.objects.create(key='waterbus.jpeg', album=public_album, timestamp=timezone.now())
        self.public_path = f"{public_album.key}/{public_photo.key}"

        private_album = Album.objects.create(key="london", public=False)
        private_photo = Photo.objects.create(key='tower.jpeg', album=private_album, timestamp=timezone.now())
        self.private_path = f"{private_album.key}/{private_photo.key}"

        self.not_found_path = "madrid/hotel.jpeg"

    def test_auth_returns_400_on_no_path(self):
        response = self.client.get("/api/_auth")
        self.assertEqual(response.status_code, 400)

    def test_auth_returns_400_on_invalid_path(self):
        testdata = [
            '/image.jpeg',
            'paris/landbus.jpeg',
        ]

        for path in testdata:
            response = self.client.get(f"/api/_auth?path=/{path}")
            self.assertEqual(response.status_code, 400)

    def _test_access(self, testdata):
        for size, path, status in testdata:
            response = self.client.get(f"/api/_auth?path=/{size}/{path}")
            self.assertEqual(response.status_code, status)


    def test_anonymous_user_can_access_scaled_photos_in_public_album(self):
        self._test_access([
            ['256', self.public_path, 204],
            ['2048', self.public_path, 204],
            ['original', self.public_path, 401],
            ['256', self.private_path, 404],
            ['2048', self.private_path, 404],
            ['original', self.private_path, 404],
            ['256', self.not_found_path, 404],
            ['2048', self.not_found_path, 404],
            ['original', self.not_found_path, 404],
        ])

    def test_authenticated_user_can_access_all_photos(self):
        login_success = self.client.login(username='test', password='test')
        self.assertTrue(login_success)

        self._test_access([
            ['256', self.public_path, 204],
            ['2048', self.public_path, 204],
            ['original', self.public_path, 204],
            ['256', self.private_path, 204],
            ['2048', self.private_path, 204],
            ['original', self.private_path, 204],
            ['256', self.not_found_path, 404],
            ['2048', self.not_found_path, 404],
            ['original', self.not_found_path, 404],
        ])


class GetAlbumsViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(username='test', password='test')

        Album.objects.create(key="venice", public=True)
        Album.objects.create(key="paris", public=True)
        Album.objects.create(key="london", public=False)

    def test_anonymous_user_can_see_public_albums(self):
        response = self.client.get("/api/albums")
        self.assertEqual(len(response.json()), 2)

    def test_authenticated_user_can_see_all_albums(self):
        login_success = self.client.login(username='test', password='test')
        self.assertTrue(login_success)

        response = self.client.get("/api/albums")
        self.assertEqual(len(response.json()), 3)
