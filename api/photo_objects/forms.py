import random
import re
import unicodedata

from django.forms import (
    CharField,
    ClearableFileInput,
    FileField,
    Form,
    HiddenInput,
    ModelForm,
    ValidationError
)
from django.utils.translation import gettext_lazy as _

from .models import Album, Photo


# From Kubernetes random postfix.
KEY_POSTFIX_CHARS = 'bcdfghjklmnpqrstvwxz2456789'
KEY_POSTFIX_LEN = 5


def slugify(input: str):
    key = unicodedata.normalize(
        'NFKD', input).encode(
        'ascii', 'ignore').decode('ascii')
    key = re.sub(r'[^a-zA-Z0-9._-]', '-', key)
    key = re.sub(r'[-_]+', '-', key)
    return key


def _postfix_generator():
    yield ''
    for _ in range(13):
        yield '-' + ''.join(
            random.choices(KEY_POSTFIX_CHARS, k=KEY_POSTFIX_LEN))


class CreateAlbumForm(ModelForm):
    key = CharField(min_length=1, widget=HiddenInput)

    class Meta:
        model = Album
        fields = ['key', 'title', 'description', 'visibility']

    def clean(self):
        super().clean()

        key = self.cleaned_data.get('key', '')
        title = self.cleaned_data.get('title', '')

        # If key is set to _new, generate a key from the title.
        if key != '_new':
            return

        if title == '':
            self.add_error(
                'title',
                ValidationError(
                    _('This field is required.'),
                    code='required'))
            return

        key = slugify(title)

        postfix_iter = _postfix_generator()
        try:
            postfix = next(postfix_iter)
            while Album.objects.filter(key=key + postfix).exists():
                postfix = next(postfix_iter)
        except StopIteration:
            self.add_error(
                "title",
                ValidationError(
                    _('Could not generate unique key from the given title. '
                      'Try to use a different title for the album.'),
                    code='unique'))
            return

        self.cleaned_data['key'] = key + postfix


class ModifyAlbumForm(ModelForm):
    class Meta:
        model = Album
        fields = ['title', 'description', 'cover_photo', 'visibility']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cover_photo'].queryset = Photo.objects.filter(
            album=self.instance)


class CreatePhotoForm(ModelForm):
    class Meta:
        model = Photo
        fields = [
            'key',
            'album',
            'title',
            'description',
            'timestamp',
            'tiny_base64']
        error_messages = {
            'album': {
                'invalid_choice': _('Album with %(value)s key does not exist.')
            }
        }


class ModifyPhotoForm(ModelForm):
    class Meta:
        model = Photo
        fields = ['title', 'description']


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class UploadPhotosForm(Form):
    photos = MultipleFileField()
