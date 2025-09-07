from base64 import b64decode
from datetime import timedelta
from io import BytesIO
from time import sleep
from unittest import mock

from django.contrib.auth import get_user_model
from PIL import Image
from urllib3.exceptions import HTTPError

from photo_objects.django.models import Album
from photo_objects.img import utcnow
from photo_objects.django.objsto import get_photo

from .utils import TestCase, add_permissions, open_test_photo, parse_timestamps


class PhotoViewTests(TestCase):
    def setUp(self):
        user = get_user_model()
        user.objects.create_user(username='no_permission', password='test')

        has_permission = user.objects.create_user(
            username='has_permission', password='test')
        add_permissions(
            has_permission,
            'add_photo',
            'change_album',
            'change_photo',
            'delete_photo',
        )

        Album.objects.create(
            key="test-photo-a",
            visibility=Album.Visibility.PUBLIC)
        Album.objects.create(
            key="test-photo-b",
            visibility=Album.Visibility.PUBLIC)

    def test_post_photo_with_non_formdata_fails(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        response = self.client.post(
            "/api/albums/test-photo-a/photos",
            "key=venice",
            content_type="text/plain")
        self.assertStatus(response, 415)

    def test_post_photo_without_files_fails(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        response = self.client.post(
            "/api/albums/test-photo-a/photos",)
        self.assertStatus(response, 400)

    def test_put_photo_fails(self):
        response = self.client.put("/api/albums/test-photo-a/photos")
        self.assertStatus(response, 405)

    def test_cannot_upload_modify_delete_photo_without_permission(self):
        self.assertRequestStatuses([
            ("POST", "/api/albums/test-photo-a/photos", 401),
            ("PATCH", "/api/albums/test-photo-a/photos/tower.jpg", 401),
            ("DELETE", "/api/albums/test-photo-a/photos/tower.jpg", 401),
        ])

        login_success = self.client.login(
            username='no_permission', password='test')
        self.assertTrue(login_success)

        self.assertRequestStatuses([
            ("POST", "/api/albums/test-photo-a/photos", 403),
            ("PATCH", "/api/albums/test-photo-a/photos/tower.jpg", 403),
            ("DELETE", "/api/albums/test-photo-a/photos/tower.jpg", 403),
        ])

    def test_upload_photo_key_cleaning(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        filename = "The Eiffel Tower.JPG"
        file = open_test_photo(filename)
        response = self.client.post(
            "/api/albums/test-photo-a/photos",
            {"The Eiffel Tower!": file})
        self.assertStatus(response, 201)
        self.assertEqual(
            response.json().get("key"),
            "test-photo-a/The-Eiffel-Tower.JPG")

    def test_upload_photo_album_not_found(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        filename = "tower.jpg"
        file = open_test_photo(filename)
        response = self.client.post(
            "/api/albums/not-found/photos",
            {filename: file})
        self.assertStatus(response, 400)

    def test_upload_photo(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        filename = "tower.jpg"
        file = open_test_photo(filename)
        response = self.client.post(
            "/api/albums/test-photo-a/photos",
            {filename: file})
        self.assertStatus(response, 201)

        photo = self.client.get(
            "/api/albums/test-photo-a/photos/tower.jpg").json()
        self.assertEqual(photo.get("timestamp"), "2024-03-20T14:28:04+00:00")
        tiny_base64 = photo.get("tiny_base64")
        width, height = Image.open(BytesIO(b64decode(tiny_base64))).size
        self.assertEqual(width, 3)
        self.assertEqual(height, 3)

        file.seek(0)
        photo_response = get_photo("test-photo-a", filename, "og")
        self.assertEqual(
            photo_response.headers['Content-Type'],
            "image/jpeg")
        self.assertEqual(
            photo_response.read(),
            file.read(),
            "Photo in the file system does not match photo uploaded to the object storage")  # noqa

        file.seek(0)
        response = self.client.post(
            "/api/albums/test-photo-a/photos",
            {filename: file})
        self.assertStatus(response, 400)

    def test_create_photo_key_validation(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        file = open_test_photo("tower.jpg")
        response = self.client.post(
            "/api/albums/test-photo-a/photos",
            {"": file})
        self.assertStatus(response, 400)

    def test_upload_invalid_photo_file(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        filename = "invalid.jpg"
        file = open_test_photo(filename)
        response = self.client.post(
            "/api/albums/test-photo-a/photos",
            {filename: file})
        self.assertStatus(response, 400)

    def test_upload_to_objsto_fails(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        filename = "tower.jpg"
        file = open_test_photo(filename)
        with mock.patch(
            "photo_objects.django.api.photo.objsto.put_photo",
            side_effect=HTTPError,
        ):
            response = self.client.post(
                "/api/albums/test-photo-a/photos",
                {filename: file})
        self.assertStatus(response, 500)

        response = self.client.get(
            "/api/albums/test-photo-a/photos/tower.jpg")
        self.assertStatus(response, 404)

        response = self.client.get(
            "/api/albums/test-photo-a/photos")
        self.assertStatus(response, 200)
        self.assertEqual(len(response.json()), 0)

    def test_get_image_scales_the_image(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        filename = "tower.jpg"
        file = open_test_photo(filename)
        response = self.client.post(
            "/api/albums/test-photo-a/photos",
            {filename: file})
        self.assertStatus(response, 201)

        # Scales image down from the original size
        small_response = self.client.get(
            "/api/albums/test-photo-a/photos/tower.jpg/img?size=sm")
        self.assertStatus(small_response, 200)
        _, height = Image.open(BytesIO(small_response.content)).size
        self.assertEqual(height, 512)

        # Does not scale image up from the original size
        large_response = self.client.get(
            "/api/albums/test-photo-a/photos/tower.jpg/img?size=lg")
        self.assertStatus(large_response, 200)
        _, height = Image.open(BytesIO(large_response.content)).size
        self.assertEqual(height, 512)

    def test_crud_actions(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        filename = "tower.jpg"
        file = open_test_photo(filename)
        response = self.client.post(
            "/api/albums/test-photo-a/photos",
            {filename: file})
        self.assertStatus(response, 201)

        # Can upload photo with the same name to a different album
        tic = utcnow()
        sleep(0.1)

        file.seek(0)
        response = self.client.post(
            "/api/albums/test-photo-b/photos",
            {filename: file})
        self.assertStatus(response, 201)

        t = parse_timestamps(response.json())
        self.assertTimestampLess(tic, t.created_at)
        self.assertTimestampLess(tic, t.updated_at)

        response = self.client.get("/api/albums/test-photo-a/photos/tower.jpg")
        self.assertStatus(response, 200)
        data = response.json()
        self.assertEqual(data.get("key"), "test-photo-a/tower.jpg")
        self.assertEqual(data.get("title"), "")
        self.assertEqual(data.get("description"), "")
        self.assertEqual(data.get("timestamp"), "2024-03-20T14:28:04+00:00")
        self.assertEqual(data.get("height"), 512)
        self.assertEqual(data.get("width"), 341)
        self.assertEqual(data.get("camera_make"), "FUJIFILM")
        self.assertEqual(data.get("camera_model"), "X-E3")
        self.assertEqual(data.get("lens_make"), "FUJIFILM")
        self.assertEqual(data.get("lens_model"), "XF23mmF2 R WR")
        self.assertEqual(data.get("focal_length"), 23.0)
        self.assertEqual(data.get("f_number"), 8.0)
        self.assertEqual(data.get("exposure_time"), 0.00025)
        self.assertEqual(data.get("iso_speed"), 800)

        tic = utcnow()
        sleep(0.1)

        req_data = dict(
            title="The Eiffel Tower",
            description="The Eiffel Tower in Paris, France")
        response = self.client.patch(
            "/api/albums/test-photo-a/photos/tower.jpg",
            content_type="application/json",
            data=req_data)
        self.assertStatus(response, 200)
        t = parse_timestamps(response.json())
        self.assertTimestampLess(t.created_at, tic)
        self.assertTimestampLess(tic, t.updated_at)
        data = {**data, **req_data, **vars(t)}
        self.assertDictEqual(response.json(), data)

        # Image file does not contain EXIF data so timestamp is the upload
        # time instead of the create time.
        filename = "havfrue.jpg"
        file = open_test_photo(filename)
        response = self.client.post(
            "/api/albums/test-photo-a/photos",
            {filename: file})
        self.assertStatus(response, 201)
        last_timestamp = response.json().get("timestamp")
        self.assertGreater(last_timestamp,
                           (utcnow() - timedelta(minutes=1)).isoformat())

        filename = "bus-stop.jpg"
        file = open_test_photo(filename)
        response = self.client.post(
            "/api/albums/test-photo-a/photos",
            {filename: file})
        self.assertStatus(response, 201)
        first_timestamp = response.json().get("timestamp")

        response = self.client.get(
            "/api/albums/test-photo-a/photos/tower.jpg/img?size=og")
        self.assertStatus(response, 200)

        response = self.client.get(
            "/api/albums/test-photo-a/photos")
        self.assertStatus(response, 200)
        self.assertListEqual(
            [i.get('filename') for i in response.json()],
            ['bus-stop.jpg', 'tower.jpg', 'havfrue.jpg'], response.content)

        response = self.client.get(
            "/api/albums/test-photo-a")
        self.assertResponseStatusAndItems(
            response, 200, {
                'first_timestamp': first_timestamp,
                'last_timestamp': last_timestamp,
                'cover_photo': 'tower.jpg',
            }
        )

        response = self.client.delete(
            "/api/albums/test-photo-a/photos/tower.jpg")
        self.assertStatus(response, 204)

        response = self.client.get(
            "/api/albums/test-photo-a")
        self.assertResponseStatusAndItems(
            response, 200, {
                'first_timestamp': first_timestamp,
                'last_timestamp': last_timestamp,
                'cover_photo': 'bus-stop.jpg',
            }
        )

        response = self.client.delete(
            "/api/albums/test-photo-a/photos/bus-stop.jpg")
        self.assertStatus(response, 204)

        response = self.client.get(
            "/api/albums/test-photo-a")
        self.assertResponseStatusAndItems(
            response, 200, {
                'first_timestamp': last_timestamp,
                'last_timestamp': last_timestamp,
                'cover_photo': 'havfrue.jpg',
            }
        )

        response = self.client.get(
            "/api/albums/test-photo-a/photos/havfrue.jpg/img?size=og")
        self.assertStatus(response, 200)

        response = self.client.get(
            "/api/albums/test-photo-a/photos/tower.jpg/img?size=og")
        self.assertStatus(response, 404)

        response = self.client.get("/api/albums/test-photo-a/photos/tower.jpg")
        self.assertStatus(response, 404)

        response = self.client.delete(
            "/api/albums/test-photo-a/photos/havfrue.jpg")
        self.assertStatus(response, 204)

        response = self.client.get(
            "/api/albums/test-photo-a")
        self.assertResponseStatusAndItems(
            response, 200, {
                'first_timestamp': None,
                'last_timestamp': None,
                'cover_photo': None,
            }
        )
