from django.forms import ClearableFileInput, FileField, Form, ModelForm
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


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
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
