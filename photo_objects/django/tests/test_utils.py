from unittest import TestCase

from minio import S3Error

from photo_objects.django import objsto
from photo_objects.django.forms import slugify


class TestUtils(TestCase):
    def test_slugify(self):
        checks = [
            ("København H", "Kbenhavn-H"),
            ("Åäö", "Aao"),
            ("_!().123", "-.123"),
            ("_MG_0736.jpg", "_MG_0736.jpg"),
            ("album__photo_-key", "album-photo-key"),
        ]

        for input, expected in checks:
            with self.subTest(input=input, expected=expected):
                self.assertEqual(slugify(input), expected)

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
