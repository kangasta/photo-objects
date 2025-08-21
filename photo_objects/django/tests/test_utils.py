from unittest import TestCase
from unittest.mock import MagicMock

from minio import S3Error

from photo_objects.django import objsto
from photo_objects.django.forms import slugify
from photo_objects.django.views.utils import meta_description


class TestUtils(TestCase):
    def test_slugify(self):
        checks = [
            ("København H", "Kbenhavn-H"),
            ("Åäö", "Aao"),
            ("_!().123", "-.123"),
            ("_MG_0736.jpg", "_MG_0736.jpg"),
            ("album__photo_-key", "album-photo-key"),
        ]

        for title, expected in checks:
            with self.subTest(input=title, expected=expected):
                self.assertEqual(slugify(title), expected)

    def test_slugify_lower(self):
        self.assertEqual(slugify("QwErTy!", True), "qwerty-")

    def test_slugify_replace_leading_underscores(self):
        self.assertEqual(
            slugify(
                "__SecretAlbum",
                replace_leading_underscores=True),
            "-SecretAlbum")

    def test_with_error_code(self):
        self.assertEqual(
            objsto.with_error_code("Failed", Exception('TEST')),
            "Failed",
        )

        e = S3Error("Test", "Test", "Test", "Test", "Test", "Test")
        self.assertEqual(
            objsto.with_error_code("Failed", e),
            "Failed (Test)",
        )

    def test_meta_description(self):
        md_multi_p = (
            "Description with **bold** and *italics*...\n\n"
            "...and multiple paragraphs")
        testdata = [
            ("Plain text description",
             "Plain text description"),
            (md_multi_p,
             "Description with bold and italics..."),
            (None,
             "A simple self-hosted photo server."),
        ]

        for description, expected in testdata:
            with self.subTest(expected=expected):
                self.assertEqual(
                    meta_description(MagicMock(), description),
                    expected)
