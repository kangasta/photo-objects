from django.contrib.sites.models import Site

from photo_objects.django.models import Album, Photo, SiteSettings

from .utils import TestCase, create_dummy_photo, temp_static_files


PHOTOS_DIRECTORY = "photos"


class OgMetaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        album = Album.objects.create(
            key="paris", visibility=Album.Visibility.PUBLIC)

        create_dummy_photo(album, "tower.jpeg")

    @temp_static_files
    def test_albums_og_meta(self):
        og_title = '<meta property="og:title" content="Test" />'

        response = self.client.get("/albums")
        self.assertNotContains(
            response,
            og_title,
            status_code=200,
            html=True)

        site = Site.objects.get(id=1)
        site.name = "Test"
        site.domain = "test.example.com"
        site.save()

        response = self.client.get("/albums")
        self.assertNotContains(
            response,
            og_title,
            status_code=200,
            html=True)

        site_settings = SiteSettings.objects.get(site=site)
        site_settings.description = "Description"
        site_settings.preview_image = Photo.objects.get(key="paris/tower.jpeg")
        site_settings.save()

        tags = [
            og_title,
            '<meta property="og:description" content="Description" />',
            '<meta property="og:image" content="https://test.example.com/img/paris/tower.jpeg/md"/>',  # noqa: E501
            '<meta property="og:url" content="https://test.example.com/albums" />',  # noqa: E501
        ]

        response = self.client.get("/albums")
        for tag in tags:
            self.assertContains(
                response,
                tag,
                status_code=200,
                html=True)
