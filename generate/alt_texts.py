from argparse import ArgumentParser
from io import BytesIO
import os
from random import shuffle
import sys

from PIL import Image
from requests import Session
import torch
import transformers
from urllib.parse import urljoin


class PhotoObjectsSession(Session):
    def __init__(self):
        super().__init__()
        self._base_url = os.getenv(
            'PHOTO_OBJECTS_URL',
            'http://localhost:8080')
        self._login()

    def request(self, method, url, *args, **kwargs):
        joined_url = urljoin(self._base_url, url)
        return super().request(method, joined_url, *args, **kwargs)

    def _get_csrf_token(self):
        response = self.get('/users/login')
        response.raise_for_status()
        return response.cookies['csrftoken']

    def _login(self):
        username = os.getenv('PHOTO_OBJECTS_USERNAME')
        password = os.getenv('PHOTO_OBJECTS_PASSWORD')
        assert username, 'Set PHOTO_OBJECTS_USERNAME environment variable'
        assert password, 'Set PHOTO_OBJECTS_PASSWORD environment variable'

        csrf_token = self._get_csrf_token()
        response = self.post(
            '/users/login',
            data={
                'csrfmiddlewaretoken': csrf_token,
                'username': username,
                'password': password,
            },
            allow_redirects=False,
        )
        assert response.status_code == 302, f'Login failed: {response.text}'

    def get_target_photos(self):
        response = self.get('/api/photo-change-requests/expected')
        response.raise_for_status()
        return response.json()

    def open_photo(self, key, size='md'):
        response = self.get(f'/img/{key}/{size}')
        response.raise_for_status()
        return Image.open(BytesIO(response.content))

    def create_photo_change_request(self, key, alt_text):
        album_key, photo_key = key.split('/', 1)

        csrf_token = self._get_csrf_token()
        response = self.post(
            f'/api/albums/{album_key}/photos/{photo_key}/change-requests',
            json={'alt_text': alt_text},
            headers={'X-CSRFToken': csrf_token},
        )
        response.raise_for_status()
        return response.json()


class Generator:
    def __init__(self, model):
        transformers.utils.logging.set_verbosity(transformers.logging.ERROR)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._pipeline = transformers.pipeline('image-to-text', model=model, device=device)

    def generate_alt_text(self, image: Image.Image) -> str:
        output = self._pipeline(image)
        text = output[0].get('generated_text', '').capitalize()
        if not text.endswith('.'):
            text += '.'
        return text


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-m','--model',
        type=str,
        default='Salesforce/blip-image-captioning-large',
        help='model to use to generate the alt texts')
    parser.add_argument('-n','--max-photos',
        type=int,
        default=25,
        help='maximum amount of photos to analyze')
    parser.add_argument('--randomize',
        action='store_true',
        help='analyze photos in random order')
    args = parser.parse_args()

    session = PhotoObjectsSession()

    photos = session.get_target_photos()
    print(f'Found {len(photos)} photos without alt text and change requests.')

    if args.randomize:
        print(f'Randomizing the order of photos.')
        shuffle(photos)

    if args.max_photos > 0:
        photos = photos[:args.max_photos]
        print(f'Generating alt text for up to {args.max_photos} photos.')

    if not photos:
        exit(0)

    print('Loading AI model...')
    generator = Generator(args.model)

    for key in photos:
        print(f'Generating alt text for {key}...')
        img = session.open_photo(key, size='md')
        alt_text = generator.generate_alt_text(img)
        session.create_photo_change_request(key, alt_text)
