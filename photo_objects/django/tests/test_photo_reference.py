from django.contrib.auth import get_user_model
from photo_objects.django.models import Album, Visibility, Story

from .utils import (
    TestCase,
    add_permissions,
    create_dummy_photo,
)


def _ref_path(story_key, photo_uuid=None):
    path = f"/api/stories/{story_key}/photo-references"
    if photo_uuid is not None:
        path += f"/{photo_uuid}"
    return path


class PhotoReferenceTests(TestCase):
    # pylint: disable=invalid-name
    def setUp(self):
        user = get_user_model()
        user.objects.create_user(username='no_permission', password='test')

        has_permission = user.objects.create_user(
            username='has_permission', password='test')
        add_permissions(
            has_permission,
            'add_photoreference',
            'change_photoreference',
            'delete_photoreference',
        )

        self.album = Album.objects.create(
            key="test-photo-reference",
            visibility=Visibility.HIDDEN)

        self.photo_1 = create_dummy_photo(self.album, "photo_1.jpg")
        self.photo_2 = create_dummy_photo(self.album, "photo_2.jpg")

        self.story = Story.objects.create(
            key="test-photo-reference",
        )

    def _create_photo_reference(
            self,
            story_key,
            photo_key,
            data=None,
            status=201):
        if data is None:
            data = {}
        data['photo'] = photo_key

        response = self.client.post(
            _ref_path(story_key),
            content_type="application/json",
            data=data
        )
        self.assertStatus(response, status)
        return response.json()

    def getReferencesLen(self, story_key):
        response = self.client.get(
            f"/api/stories/{story_key}/photo-references")
        self.assertStatus(response, 200)
        return len(response.json())

    def assertReferencesLen(self, story_key, expected_len):
        self.assertEqual(self.getReferencesLen(story_key), expected_len)

    def test_create_permissions(self):
        login_success = self.client.login(
            username='no_permission', password='test')
        self.assertTrue(login_success)

        self._create_photo_reference(
            self.story.key,
            self.photo_1.key,
            status=403
        )

    def test_crud_actions(self):
        login_success = self.client.login(
            username='has_permission', password='test')
        self.assertTrue(login_success)

        n = self.getReferencesLen(self.story.key)

        self._create_photo_reference(
            self.story.key,
            self.photo_1.key,
            status=201)
        self.assertReferencesLen(self.story.key, n + 1)

        # Cannot add reference to the same photo twice
        self._create_photo_reference(
            self.story.key,
            self.photo_1.key,
            status=400)
        self.assertReferencesLen(self.story.key, n + 1)

        self._create_photo_reference(
            self.story.key,
            self.photo_2.key,
            status=201)
        self.assertReferencesLen(self.story.key, n + 2)

        response = self.client.patch(
            _ref_path(self.story.key, self.photo_1.uuid),
            content_type="application/json",
            data=dict(
                title="Renamed title",
                description="New description",
            )
        )
        self.assertStatus(response, 200)

        response = self.client.delete(
            _ref_path(self.story.key, self.photo_1.uuid))
        self.assertStatus(response, 204)

        self.assertReferencesLen(self.story.key, n + 1)

        login_success = self.client.login(
            username='no_permission', password='test')
        self.assertTrue(login_success)

        response = self.client.patch(
            _ref_path(self.story.key, self.photo_2.uuid),
            content_type="application/json",
            data=dict(
                title="Renamed title",
                description="New description",
            )
        )
        self.assertStatus(response, 403)

        response = self.client.delete(
            _ref_path(self.story.key, self.photo_2.uuid))
        self.assertStatus(response, 403)

        self.assertReferencesLen(self.story.key, n + 1)
