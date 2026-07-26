from django.contrib.auth import get_user_model

from .utils import (
    TestCase,
    add_permissions,
)


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
