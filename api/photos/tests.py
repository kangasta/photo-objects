from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Album, Photo


CANAL_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAMAAAAFBAMAAAByX0uRAAAALVBMVEW1no/d4OiTc2jAoozGvbaOZ06igXB5alqJYEFXUUJ6fn9zVT9PVUBhe4U4LyJRWPqlAAAAF0lEQVQI12NgVGAwCWBIb2CYtYHh7AMAFg0EhKs+JLkAAAAASUVORK5CYII="
TOWER_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAMAAAAFBAMAAAByX0uRAAAALVBMVEVZl898sOJgm9CSvuucpraRtdqer8OTdWWcrL+Zb06UZUaOkZpeSTtpRzBbXmMTFH6IAAAAF0lEQVQI12NgVGAwCWBIb2CYtYHh7AMAFg0EhKs+JLkAAAAASUVORK5CYII="


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
            ['384', self.public_path, 204],
            ['2048', self.public_path, 204],
            ['original', self.public_path, 401],
            ['384', self.private_path, 404],
            ['2048', self.private_path, 404],
            ['original', self.private_path, 404],
            ['384', self.not_found_path, 404],
            ['2048', self.not_found_path, 404],
            ['original', self.not_found_path, 404],
        ])

    def test_authenticated_user_can_access_all_photos(self):
        login_success = self.client.login(username='test', password='test')
        self.assertTrue(login_success)

        self._test_access([
            ['384', self.public_path, 204],
            ['2048', self.public_path, 204],
            ['original', self.public_path, 204],
            ['384', self.private_path, 204],
            ['2048', self.private_path, 204],
            ['original', self.private_path, 204],
            ['384', self.not_found_path, 404],
            ['2048', self.not_found_path, 404],
            ['original', self.not_found_path, 404],
        ])


class ViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(username='test', password='test')

        album = Album.objects.create(key="venice", public=True)
        Album.objects.create(key="paris", public=True)
        Album.objects.create(key="london", public=False)

        Photo.objects.create(key='tower.jpeg', album=album, timestamp=timezone.now(), tiny_base64=TOWER_BASE64)
        Photo.objects.create(key='canal.jpeg', album=album, timestamp=timezone.now(), tiny_base64=CANAL_BASE64)
        Photo.objects.create(key='gondola.jpeg', album=album, timestamp=timezone.now())
        Photo.objects.create(key='church.jpeg', album=album, timestamp=timezone.now())

    def test_anonymous_user_can_see_public_albums(self):
        response = self.client.get("/api/albums")
        self.assertEqual(len(response.json()), 2)

    def test_authenticated_user_can_see_all_albums(self):
        login_success = self.client.login(username='test', password='test')
        self.assertTrue(login_success)

        response = self.client.get("/api/albums")
        self.assertEqual(len(response.json()), 3)

    def test_get_albums_lists_processed_photos(self):
        data = self.client.get("/api/albums").json()
        album = next(i for i in data if i.get('key') == 'venice')

        photos = album.get('photos')
        self.assertEqual(len(photos), 2)

        photo = next(i for i in photos if i.get('key') == 'tower.jpeg')
        self.assertEqual(photo.get('album'), 'venice')

    def test_get_pending_photos(self):
        data = self.client.get("/api/photos/pending").json()
        self.assertEqual(len(data), 2)
