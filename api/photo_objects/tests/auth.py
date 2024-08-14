from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from photo_objects.models import Album, Photo


def _path_fn(album, photo):
    return lambda size: f"{album}/{photo}/{size}"


class AuthViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(username='test', password='test')

        public_album = Album.objects.create(
            key="venice", visibility=Album.Visibility.PUBLIC)
        public_photo = Photo.objects.create(
            key='waterbus.jpeg',
            album=public_album,
            timestamp=timezone.now())
        self.public_path = _path_fn(public_album.key, public_photo.key)

        hidden_album = Album.objects.create(
            key="paris", visibility=Album.Visibility.HIDDEN)
        hidden_photo = Photo.objects.create(
            key='bridge.jpeg',
            album=hidden_album,
            timestamp=timezone.now())
        self.hidden_path = _path_fn(hidden_album.key, hidden_photo.key)

        private_album = Album.objects.create(
            key="london", visibility=Album.Visibility.PRIVATE)
        private_photo = Photo.objects.create(
            key='tower.jpeg',
            album=private_album,
            timestamp=timezone.now())
        self.private_path = _path_fn(private_album.key, private_photo.key)

        self.not_found_path = _path_fn("madrid", "hotel")

    def test_auth_returns_403_on_no_path(self):
        response = self.client.get("/_auth")
        self.assertEqual(response.status_code, 403)

    def test_auth_returns_403_on_invalid_path(self):
        testdata = [
            '/image.jpeg',
            'paris/landbus.jpeg',
        ]

        for path in testdata:
            response = self.client.get(f"/_auth?path=/{path}")
            self.assertEqual(response.status_code, 403)

    def _test_access(self, testdata):
        for path, status in testdata:
            with self.subTest(path=path):
                response = self.client.get(f"/_auth?path=/{path}")
                self.assertEqual(response.status_code, status)

    def test_anonymous_user_access(self):
        self._test_access([
            [self.public_path('asd'), 403],
            [self.public_path('sm'), 204],
            [self.public_path('lg'), 204],
            [self.public_path('og'), 403],
            [self.hidden_path('sm'), 204],
            [self.hidden_path('lg'), 204],
            [self.hidden_path('og'), 403],
            [self.private_path('sm'), 403],
            [self.private_path('lg'), 403],
            [self.private_path('og'), 403],
            [self.not_found_path('sm'), 403],
            [self.not_found_path('lg'), 403],
            [self.not_found_path('og'), 403],
        ])

    def test_authenticated_user_can_access_all_photos(self):
        login_success = self.client.login(username='test', password='test')
        self.assertTrue(login_success)

        self._test_access([
            [self.public_path('asd'), 403],
            [self.public_path('sm'), 204],
            [self.public_path('lg'), 204],
            [self.public_path('og'), 204],
            [self.hidden_path('sm'), 204],
            [self.hidden_path('lg'), 204],
            [self.hidden_path('og'), 204],
            [self.private_path('sm'), 204],
            [self.private_path('lg'), 204],
            [self.private_path('og'), 204],
            [self.not_found_path('sm'), 403],
            [self.not_found_path('lg'), 403],
            [self.not_found_path('og'), 403],
        ])
