from django.contrib.auth import get_user_model

from photo_objects.django.models import Album

from .utils import TestCase, create_dummy_photo


def _path_fn(album, photo):
    return lambda size: f"{size}/{album}/{photo}"


class AuthViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model()
        user.objects.create_user(username='test-auth', password='test')

        public_album = Album.objects.create(
            key="test-auth-public", visibility=Album.Visibility.PUBLIC)
        public_photo = create_dummy_photo(public_album, "waterbus.jpeg")
        cls.public_path = _path_fn(public_album.key, public_photo.filename)

        hidden_album = Album.objects.create(
            key="test-auth-hidden", visibility=Album.Visibility.HIDDEN)
        hidden_photo = create_dummy_photo(hidden_album, "bridge.jpeg")
        cls.hidden_path = _path_fn(hidden_album.key, hidden_photo.filename)

        private_album = Album.objects.create(
            key="test-auth-private", visibility=Album.Visibility.PRIVATE)
        private_photo = create_dummy_photo(private_album, "tower.jpeg")
        cls.private_path = _path_fn(private_album.key, private_photo.filename)

        admin_album = Album.objects.create(
            key="test-auth-admin", visibility=Album.Visibility.ADMIN)
        admin_photo = create_dummy_photo(admin_album, "church.jpeg")
        cls.admin_path = _path_fn(admin_album.key, admin_photo.filename)

        cls.not_found_path = _path_fn("madrid", "hotel")

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
            [self.admin_path('sm'), 204],
            [self.admin_path('lg'), 204],
            [self.admin_path('og'), 403],
            [self.not_found_path('sm'), 403],
            [self.not_found_path('lg'), 403],
            [self.not_found_path('og'), 403],
        ])

    def test_authenticated_user_can_access_all_photos(self):
        login_success = self.client.login(
            username='test-auth', password='test')
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
            [self.admin_path('sm'), 204],
            [self.admin_path('lg'), 204],
            [self.admin_path('og'), 204],
            [self.not_found_path('sm'), 403],
            [self.not_found_path('lg'), 403],
            [self.not_found_path('og'), 403],
        ])
