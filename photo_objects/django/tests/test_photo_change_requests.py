from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from photo_objects.django.models import Album


from .utils import TestCase, create_dummy_photo


TEST_PREFIX = "test-photo-change-request"


def _filter_by_test_prefix(items):
    return [item for item in items if item.startswith(TEST_PREFIX)]


class PhotoChangeRequestTests(TestCase):
    def setUp(self):
        user = get_user_model()
        user.objects.create_user(username='no_permission', password='test')

        user.objects.create_user(
            username='superuser',
            password='test',
            is_staff=True,
            is_superuser=True)

        has_permission = user.objects.create_user(
            username='has_permission', password='test')
        permissions = [
            'change_photo',
            'delete_photochangerequest',
        ]
        for permission in permissions:
            has_permission.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label='photo_objects',
                    codename=permission))

        self.private_album = Album.objects.create(
            key=f"{TEST_PREFIX}-private", visibility=Album.Visibility.PRIVATE)
        self.admin_album = Album.objects.create(
            key=f"{TEST_PREFIX}-admin", visibility=Album.Visibility.ADMIN)

        create_dummy_photo(self.private_album, "001.jpg")
        create_dummy_photo(self.private_album, "002.jpg")
        create_dummy_photo(self.admin_album, "003.jpg")

    def test_expected_photo_change_requests(self):
        tests = [
            ("no_permission", 403, 0),
            ("has_permission", 200, 2),
            ("superuser", 200, 3),
        ]

        for username, expected_status, expected_count in tests:
            with self.subTest(username=username):
                self.client.login(username=username, password='test')
                response = self.client.get(
                    '/api/photo-change-requests/expected')
                self.assertStatus(response, expected_status)
                if expected_status == 200:
                    photos = _filter_by_test_prefix(response.json())
                    self.assertEqual(len(photos), expected_count)

    def test_create_photo_change_requests(self):
        self.client.login(username="superuser", password='test')

        response = self.client.get(
            '/api/photo-change-requests/expected')
        self.assertEqual(response.status_code, 200)
        photos = _filter_by_test_prefix(response.json())
        self.assertEqual(len(photos), 3)

        response = self.client.post(
            f'/api/albums/{TEST_PREFIX}-private/photos/001.jpg/change-requests',  # noqa: E501
            data={'alt_text': ''},
            content_type="application/json")
        self.assertStatus(response, 400)

        response = self.client.post(
            f'/api/albums/{TEST_PREFIX}-private/photos/001.jpg/change-requests',  # noqa: E501
            data={'alt_text': 'Test alt text'},
            content_type="application/json")
        self.assertStatus(response, 201)

        response = self.client.get(
            '/api/photo-change-requests/expected')
        self.assertEqual(response.status_code, 200)
        photos = _filter_by_test_prefix(response.json())
        self.assertEqual(len(photos), 2)
