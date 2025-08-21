from io import BytesIO

from PIL import Image

from photo_objects.django.conf import DEFAULT_SM
from photo_objects.img import scale_photo

from .utils import TestCase


class ImgTests(TestCase):
    def test_scale_photo(self):
        testdata = [
            ((1000, 200), (300, 200)),
            ((600, 2000), (341, 512)),
            ((1000, 1000), (512, 512)),
        ]

        for size, expected in testdata:
            with self.subTest(w=size[0], h=size[1]):
                original = BytesIO()
                image = Image.new("RGB", size, color="red")
                image.save(original, format="JPEG")
                original.seek(0)

                scaled = scale_photo(original, "output.jpg", **DEFAULT_SM)
                actual = Image.open(scaled).size

                self.assertEqual(actual, expected)
