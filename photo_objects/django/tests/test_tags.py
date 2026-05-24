from django.contrib.auth import get_user_model

from photo_objects.django.models import Album, Tag

from .utils import (
    TestCase,
    add_permissions,
)


class TagTests(TestCase):
    def setUp(self):
        user = get_user_model()
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
            key="test-tag",
            visibility=Album.Visibility.PUBLIC)

    def test_unused_tags_are_deleted(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        response = self._upload_photo("test-tag", "tower.jpg")

        req_data = dict(
            tags=["landmark", "Paris", "France", "tower"],)
        response = self.client.patch(
            "/api/albums/test-tag/photos/tower.jpg",
            content_type="application/json",
            data=req_data)
        self.assertStatus(response, 200)

        self.assertEqual(Tag.objects.count(), 4)

        req_data = dict(
            tags=["landmark", "tower"],)
        response = self.client.patch(
            "/api/albums/test-tag/photos/tower.jpg",
            content_type="application/json",
            data=req_data)
        self.assertStatus(response, 200)

        self.assertEqual(Tag.objects.count(), 2)
