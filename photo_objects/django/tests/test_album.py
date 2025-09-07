import json
from time import sleep

from django.contrib.auth import get_user_model

from photo_objects.django.models import Album
from photo_objects.img import utcnow

from .utils import (
    TestCase,
    add_permissions,
    parse_timestamps,
    create_dummy_photo,
    open_test_photo
)


PHOTOS_DIRECTORY = "photos"


class ViewVisibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model()
        user.objects.create_user(username='test-visibility', password='test')
        user.objects.create_user(
            username='test-staff-visibility',
            password='test',
            is_staff=True)

        album = Album.objects.create(
            key="venice", visibility=Album.Visibility.PUBLIC)
        Album.objects.create(
            key="test-visibility-public",
            visibility=Album.Visibility.PUBLIC)
        Album.objects.create(
            key="test-visibility-private",
            visibility=Album.Visibility.PRIVATE)
        Album.objects.create(
            key="test-visibility-hidden",
            visibility=Album.Visibility.HIDDEN)
        Album.objects.create(
            key="test-visibility-admin",
            visibility=Album.Visibility.ADMIN)

        create_dummy_photo(album, "tower.jpeg")
        create_dummy_photo(album, "canal.jpeg")
        create_dummy_photo(album, "gondola.jpeg")
        create_dummy_photo(album, "church.jpeg")

    def test_anonymous_user_can_see_public_albums(self):
        response = self.client.get("/api/albums")
        self.assertEqual(len(response.json()), 2)

    def test_authenticated_user_can_see_all_non_admin_albums(self):
        login_success = self.client.login(
            username='test-visibility', password='test')
        self.assertTrue(login_success)

        response = self.client.get("/api/albums")
        self.assertEqual(len(response.json()), 4)

    def test_staff_user_can_see_all_albums(self):
        login_success = self.client.login(
            username='test-staff-visibility', password='test')
        self.assertTrue(login_success)

        response = self.client.get("/api/albums")
        self.assertEqual(len(response.json()), 5)

    def test_anonymous_user_get_album_get_photos(self):
        self.assertRequestStatuses([
            ("GET", "/api/albums/test-visibility-public/photos", 200),
            ("GET", "/api/albums/test-visibility-private/photos", 404),
            ("GET", "/api/albums/test-visibility-hidden/photos", 200),
            ("GET", "/api/albums/test-visibility-admin/photos", 404),
            ("GET", "/api/albums/test-visibility-public", 200),
            ("GET", "/api/albums/test-visibility-private", 404),
            ("GET", "/api/albums/test-visibility-hidden", 200),
            ("GET", "/api/albums/test-visibility-admin", 404),
        ])

    def test_get_photos_lists_all_photos(self):
        photos = self.client.get("/api/albums/venice/photos").json()
        self.assertEqual(len(photos), 4)

        photo = next(i for i in photos if i.get('key') == 'venice/tower.jpeg')
        self.assertEqual(photo.get('album'), 'venice', photos)


class AlbumViewTests(TestCase):
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
        add_permissions(
            has_permission,
            'add_album',
            'add_photo',
            'change_album',
            'delete_album',
            'delete_photo',
        )

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
            data=dict(key="oslo"))
        self.assertEqual(data.status_code, 201, json.dumps(data.json()))

        album = self.client.get("/api/albums/oslo").json()
        self.assertEqual(
            album.get("visibility"),
            Album.Visibility.PRIVATE.value)

    def test_cannot_use_admin_visibility_as_normal_user(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        data = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(
                key="stockholm",
                visibility="private"))
        self.assertEqual(data.status_code, 201, json.dumps(data.json()))

        for username, visibility, post_status, patch_status in [
            ("has_permission", "", 400, 400),
            # ("has_permission", "admin", 400, 400),
            ("superuser", "", 201, 200),
            # ("superuser", "admin", 201, 200),
            # The album now has admin visibility and should thus return 404 for
            # non admin user.
            ("has_permission", "", 400, 404),
        ]:
            with self.subTest(username=username, visibility=visibility):
                login_success = self.client.login(
                    username=username, password='test')
                self.assertTrue(login_success)

                data = self.client.post(
                    "/api/albums",
                    content_type="application/json",
                    data=dict(
                        key="oslo",
                        visibility=visibility))
                self.assertEqual(
                    data.status_code,
                    post_status,
                    json.dumps(
                        data.json()))

                data = self.client.patch(
                    "/api/albums/stockholm",
                    content_type="application/json",
                    data=dict(visibility=visibility))
                self.assertEqual(
                    data.status_code,
                    patch_status,
                    json.dumps(
                        data.json()))

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

        for key in ["", "#invalid", "()", "_reserved"]:
            response = self.client.post(
                "/api/albums",
                content_type="application/json",
                data=dict(key=key)
            )
            self.assertStatus(response, 400)

        response = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(key="oslo"))
        self.assertStatus(response, 201)
        self.assertEqual(response.json().get("visibility"), "private")

        response = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(key="oslo"))
        self.assertStatus(response, 400)

    def test_create_album_auto_key(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        response = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(key="_new"))
        self.assertStatus(response, 400)

        key_re = r"aleksis-kiven-katu-[a-z0-9]{5}"

        response = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(key="_new", title="Aleksis Kiven katu"))
        self.assertStatus(response, 201)
        key_1 = response.json().get("key")
        self.assertRegex(key_1, key_re)

        response = self.client.post(
            "/api/albums",
            content_type="application/json",
            data=dict(key="_new", title="Aleksis Kiven katu"))
        self.assertStatus(response, 201)
        key_2 = response.json().get("key")
        self.assertRegex(key_2, key_re)
        self.assertNotEqual(key_1, key_2)

    def test_crud_actions(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        tic = utcnow()
        sleep(0.1)

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

        created_data = response.json()
        for key, value in data.items():
            self.assertEqual(created_data.get(key), value)
        data = created_data

        t = parse_timestamps(data)
        self.assertTimestampLess(tic, t.created_at)
        self.assertTimestampLess(tic, t.updated_at)

        tic = utcnow()
        sleep(0.1)

        req_data = dict(
            title="Copenhagen",
            description="Copenhagen (København) is the capital of Denmark.")
        response = self.client.patch(
            "/api/albums/copenhagen",
            content_type="application/json",
            data=req_data)
        self.assertStatus(response, 200)

        t = parse_timestamps(response.json())
        self.assertTimestampLess(t.created_at, tic)
        self.assertTimestampLess(tic, t.updated_at)

        response = self.client.get("/api/albums/copenhagen")
        self.assertStatus(response, 200)
        data = {**data, **req_data, **vars(t)}
        self.assertDictEqual(response.json(), data)

        req_data = dict(visibility="public")
        response = self.client.patch(
            "/api/albums/copenhagen",
            content_type="application/json",
            data=req_data)
        self.assertStatus(response, 200)
        t = parse_timestamps(response.json())
        data = {**data, **req_data, **vars(t)}
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
