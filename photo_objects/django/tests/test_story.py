from django.contrib.auth import get_user_model

from photo_objects.django.models import (
    Album,
    PhotoReference,
    Story,
)

from .utils import (
    VISIBILITIES,
    TestCase,
    add_permissions,
    create_dummy_photo,
)


class StoryVisibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = get_user_model()
        user.objects.create_user(
            username='test-story-visibility',
            password='test')
        user.objects.create_user(
            username='test-story-staff-visibility',
            password='test',
            is_staff=True)

        cls.albums = []

        for label, visibility in VISIBILITIES.items():
            cls.albums.append(Album.objects.create(
                key=f"test-story-visibility-{label}-album",
                visibility=visibility))
            story = Story.objects.create(
                key=f"test-story-visibility-{label}",
                visibility=visibility)

        story = Story.objects.get(key="test-story-visibility-public")
        for album in cls.albums:
            photo = create_dummy_photo(album, "photo.jpeg")
            PhotoReference.objects.create(story=story, photo=photo)

    def test_story_visibility(self):
        tests = [
            (None, 1),
            ("test-story-visibility", 3),
            ("test-story-staff-visibility", 4),
        ]

        for username, count in tests:
            with self.subTest(username=username):
                if username is not None:
                    login_success = self.client.login(
                        username=username, password='test')
                    self.assertTrue(login_success)

                response = self.client.get("/api/stories")
                self.assertEqual(len(response.json()), count)

    def test_photo_visibility(self):
        tests = [
            (None, 2),
            ("test-story-visibility", 3),
            ("test-story-staff-visibility", 4),
        ]

        for username, count in tests:
            with self.subTest(username=username):
                if username is not None:
                    login_success = self.client.login(
                        username=username, password='test')
                    self.assertTrue(login_success)

                key = "test-story-visibility-public"
                response = self.client.get(
                    f"/api/stories/{key}/photo-references")
                self.assertEqual(len(response.json()), count)


class StoryTests(TestCase):
    def setUp(self):
        user = get_user_model()
        user.objects.create_user(username='no_permission', password='test')

        has_permission = user.objects.create_user(
            username='has_permission', password='test')
        add_permissions(
            has_permission,
            'add_story',
            'change_story',
            'delete_story',
        )

    def test_create_permissions(self):
        login_success = self.client.login(
            username='no_permission', password='test')
        self.assertTrue(login_success)

        response = self.client.post(
            "/api/stories",
            content_type="application/json",
            data=dict(key="test-story-create"))
        self.assertStatus(response, 403)

    def test_crud_actions(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        key_re = r"test-story-crud-[a-z0-9]{5}"

        response = self.client.post(
            "/api/stories",
            content_type="application/json",
            data=dict(key="_new", title="Test story CRUD"))
        self.assertStatus(response, 201)
        data = response.json()

        key = data.get("key")
        self.assertRegex(key, key_re)

        response = self.client.patch(
            f"/api/stories/{key}",
            content_type="application/json",
            data=dict(priority=12345))
        self.assertStatus(response, 200)
        data = response.json()
        self.assertEqual(data.get("title"), "Test story CRUD")
        self.assertEqual(data.get("priority"), 12345)

        response = self.client.get(f"/api/stories/{key}")
        self.assertStatus(response, 200)

        response = self.client.delete(f"/api/stories/{key}")
        self.assertStatus(response, 204)

        response = self.client.get(f"/api/stories/{key}")
        self.assertStatus(response, 404)
