from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Album, Photo


class CreateAlbumForm(ModelForm):
    class Meta:
        model = Album
        fields = ['key', 'title', 'description', 'visibility']


class ModifyAlbumForm(ModelForm):
    class Meta:
        model = Album
        fields = ['title', 'description', 'visibility']


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
