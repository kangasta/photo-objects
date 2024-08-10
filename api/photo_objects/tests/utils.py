import os

from django.test import TestCase as DjangoTestCase


def open_test_photo(filename):
    path = os.path.join(
        os.path.dirname(
            os.path.realpath(__file__)),
        "photos",
        filename)
    return open(path, "rb")


class TestCase(DjangoTestCase):
    def assertStatus(self, response, status):
        self.assertEqual(response.status_code, status, response.content)
