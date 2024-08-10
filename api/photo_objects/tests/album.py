import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone

from photo_objects.models import Album, Photo

from .utils import TestCase, open_test_photo


CANAL_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAMAAAAFBAMAAAByX0uRAAAALVBMVEW1no/d4OiTc2jAoozGvbaOZ06igXB5alqJYEFXUUJ6fn9zVT9PVUBhe4U4LyJRWPqlAAAAF0lEQVQI12NgVGAwCWBIb2CYtYHh7AMAFg0EhKs+JLkAAAAASUVORK5CYII="  # noqa
TOWER_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAMAAAAFBAMAAAByX0uRAAAALVBMVEVZl898sOJgm9CSvuucpraRtdqer8OTdWWcrL+Zb06UZUaOkZpeSTtpRzBbXmMTFH6IAAAAF0lEQVQI12NgVGAwCWBIb2CYtYHh7AMAFg0EhKs+JLkAAAAASUVORK5CYII="  # noqa

PHOTOS_DIRECTORY = "photos"


class ViewVisibilityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(username='test', password='test')

        album = Album.objects.create(
            key="venice", visibility=Album.Visibility.PUBLIC)
        Album.objects.create(key="paris", visibility=Album.Visibility.PUBLIC)
        Album.objects.create(key="london", visibility=Album.Visibility.PRIVATE)
        Album.objects.create(key="berlin", visibility=Album.Visibility.HIDDEN)

        Photo.objects.create(
            key='tower.jpeg',
            album=album,
            timestamp=timezone.now(),
            tiny_base64=TOWER_BASE64)
        Photo.objects.create(
            key='canal.jpeg',
            album=album,
            timestamp=timezone.now(),
            tiny_base64=CANAL_BASE64)
        Photo.objects.create(
            key='gondola.jpeg',
            album=album,
            timestamp=timezone.now())
        Photo.objects.create(
            key='church.jpeg',
            album=album,
            timestamp=timezone.now())

    def test_anonymous_user_can_see_public_albums(self):
        response = self.client.get("/api/albums")
        self.assertEqual(len(response.json()), 2)

    def test_authenticated_user_can_see_all_albums(self):
        login_success = self.client.login(username='test', password='test')
        self.assertTrue(login_success)

        response = self.client.get("/api/albums")
        self.assertEqual(len(response.json()), 4)

    def test_anonymous_user_get_album_get_photos(self):
        checks = [
            ("/api/albums/paris/photos", 200),
            ("/api/albums/london/photos", 404),
            ("/api/albums/berlin/photos", 404),
            ("/api/albums/paris", 200),
            ("/api/albums/london", 404),
            ("/api/albums/berlin", 404),
        ]

        for path, status in checks:
            with self.subTest(path=path, status=status):
                response = self.client.get(path)
                self.assertStatus(response, status)

    def test_get_photos_lists_all_photos(self):
        photos = self.client.get("/api/albums/venice/photos").json()
        self.assertEqual(len(photos), 4)

        photo = next(i for i in photos if i.get('key') == 'tower.jpeg')
        self.assertEqual(photo.get('album'), 'venice')


class AlbumViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        User.objects.create_user(username='no_permission', password='test')

        has_permission = User.objects.create_user(
            username='has_permission', password='test')
        permissions = [
            'add_album',
            'add_photo',
            'change_album',
            'delete_album',
            'delete_photo']
        for permission in permissions:
            has_permission.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label='photo_objects',
                    codename=permission))

    def test_post_album_with_non_json_data_fails(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        data = self.client.post(
            "/api/albums",
            "key=venice",
            content_type="text/plain")
        self.assertEqual(data.status_code, 415, json.dumps(data.json()))

    def test_post_album_with_invalid_json_data_fails(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        data = self.client.post(
            "/api/albums",
            "key: venice",
            content_type="application/json")
        self.assertEqual(data.status_code, 400, json.dumps(data.json()))

    def test_put_album_fails(self):
        data = self.client.put("/api/albums")
        self.assertEqual(data.status_code, 405, json.dumps(data.json()))

    def test_cannot_create_album_without_permission(self):
        data = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(
                key="oslo"))
        self.assertEqual(data.status_code, 401, json.dumps(data.json()))

        login_success = self.client.login(
            username='no_permission', password='test')
        self.assertTrue(login_success)

        data = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(
                key="oslo"))
        self.assertEqual(data.status_code, 403, json.dumps(data.json()))

        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        data = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(
                key="oslo"))
        self.assertEqual(data.status_code, 201, json.dumps(data.json()))

    def test_create_album(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        data = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(
                key="oslo",
                visibility="hidden",
                title="title",
                description="description"))
        self.assertEqual(data.status_code, 201, json.dumps(data.json()))

        album = self.client.get("/api/albums/oslo").json()
        self.assertEqual(
            album.get("visibility"),
            Album.Visibility.HIDDEN.value)
        self.assertEqual(album.get("title"), "title")
        self.assertEqual(album.get("description"), "description")

    def test_create_album_key_validation(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        data = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(
                key=""))
        self.assertEqual(data.status_code, 400, json.dumps(data.json()))

        data = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(
                key="oslo"))
        self.assertEqual(data.status_code, 201, json.dumps(data.json()))

        data = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(
                key="oslo"))
        self.assertEqual(data.status_code, 409, json.dumps(data.json()))

    def test_crud_actions(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        data = dict(
            key="copenhagen",
            visibility="hidden",
            title="title",
            description="description")
        response = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=data)
        self.assertStatus(response, 201)

        req_data = dict(
            title="Copenhagen",
            description="Copenhagen (København) is the capital of Denmark.")
        response = self.client.patch(
            "/api/albums/copenhagen",
            content_type="application/json",
            data=req_data)
        self.assertStatus(response, 200)

        response = self.client.get("/api/albums/copenhagen")
        self.assertStatus(response, 200)
        data = {**data, **req_data}
        self.assertDictEqual(response.json(), data)

        req_data = dict(visibility="public")
        response = self.client.patch(
            "/api/albums/copenhagen",
            content_type="application/json",
            data=req_data)
        self.assertStatus(response, 200)
        data = {**data, **req_data}
        self.assertDictEqual(response.json(), data)

        filename = "havfrue.jpg"
        file = open_test_photo(filename)
        response = self.client.post(
            "/api/albums/copenhagen/photos",
            {filename: file})
        self.assertStatus(response, 201)

        response = self.client.delete("/api/albums/copenhagen")
        self.assertStatus(response, 409)

        response = self.client.delete(
            "/api/albums/copenhagen/photos/havfrue.jpg")
        self.assertStatus(response, 204)

        response = self.client.delete("/api/albums/copenhagen")
        self.assertStatus(response, 204)
