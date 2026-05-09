from django.contrib.sites.models import Site

from photo_objects.django.models import Album, Photo, SiteSettings

from .utils import TestCase, create_dummy_photo, temp_static_files


class OgMetaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        album = Album.objects.create(
            title="Paris", key="paris", visibility=Album.Visibility.PUBLIC)

        cls.photo = create_dummy_photo(album, "tower.jpeg")

    def _configure_site(self):
        site = Site.objects.get(id=1)
        site.name = "Test"
        site.domain = "test.example.com"
        site.save()

        return site

    @temp_static_files
    def test_albums_og_meta(self):
        og_title = '<meta property="og:title" content="Test" />'

        response = self.client.get("/albums")
        self.assertNotContains(
            response,
            og_title,
            status_code=200,
            html=True)

        site = self._configure_site()

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
            f'<meta property="og:image" content="https://test.example.com/img/_uuid/{self.photo.uuid}/md"/>',  # noqa: E501
            '<meta property="og:url" content="https://test.example.com/albums" />',  # noqa: E501
        ]

        response = self.client.get("/albums")
        for tag in tags:
            self.assertContains(
                response,
                tag,
                status_code=200,
                html=True)

    @temp_static_files
    def test_photo_default_og_meta(self):
        self._configure_site()

        month_year = self.photo.timestamp.strftime("%B %Y")
        og_desc_album = (
            '<meta property="og:description" content="Photo from '
            f'{month_year} in Paris album." />')
        og_desc_photo = (
            '<meta property="og:description" content="Photo from '
            f'{month_year}." />')

        response = self.client.get("/albums/paris/photos/tower.jpeg")
        self.assertContains(
            response,
            og_desc_album,
            status_code=200,
            html=True)
        self.assertNotContains(
            response,
            og_desc_photo,
            status_code=200,
            html=True)

        response = self.client.get(f"/photos/{self.photo.uuid}")
        self.assertNotContains(
            response,
            og_desc_album,
            status_code=200,
            html=True)
        self.assertContains(
            response,
            og_desc_photo,
            status_code=200,
            html=True)
