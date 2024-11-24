from unittest import TestCase

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
