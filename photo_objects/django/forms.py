import random

from django import forms
from django.forms import (
    CharField,
    HiddenInput,
    ModelForm,
    RadioSelect,
    ValidationError,
)
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from photo_objects.utils import slugify

from .models import Album, Photo, PhotoChangeRequest


# From Kubernetes random postfix.
KEY_POSTFIX_CHARS = 'bcdfghjklmnpqrstvwxz2456789'
KEY_POSTFIX_LEN = 5

ALBUM_TITLE_HELP = _(
    'When creating a new album, album key is generated based on the title. '
    'Modifying the title later does not change the album key.'
)
ALT_TEXT_HELP = _('Alternative text content for the photo.')


def _postfix_generator():
    for _ in range(13):
        yield '-' + ''.join(
            random.choices(KEY_POSTFIX_CHARS, k=KEY_POSTFIX_LEN))


def description_help(resource):
    return {'description': _(
        f'Optional description for the {resource}. If defined, the '
        f'description is visible on the {resource} details page. Use Markdown '
        'syntax to format the description.'),
    }


def visibility_help(visibility: str):
    visibility = Album.Visibility(visibility)
    if visibility == Album.Visibility.PUBLIC:
        return _(
            'The album is visible to anyone without authentication.')
    if visibility == Album.Visibility.HIDDEN:
        return _(
            'The album is visible to anyone with the link. Only '
            'authenticated users can see the album in albums list.')
    if visibility == Album.Visibility.PRIVATE:
        return _(
            'The album is only visible to authenticated users.')
    if visibility == Album.Visibility.ADMIN:
        return _(
            'The album is only visible to admin users.')
    return None


class VisibilityRadioSelect(RadioSelect):
    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex=subindex,
            attrs=attrs)
        option['label'] = mark_safe(f'''
<div>
  <span class="label">{label}</span>
  <p class="helptext">{visibility_help(option.get('value'))}</p>
</div>''')
        return option


def _check_admin_visibility(form):
    if form.user and form.user.is_staff:
        return

    if form.data.get("visibility") == Album.Visibility.ADMIN:
        form.add_error(
            'visibility',
            ValidationError(
                _(
                    'Can not set admin visibility as non-admin user. Select a '
                    'different visibility setting.'),
                code='invalid'))
        return


class CreateAlbumForm(ModelForm):
    key = CharField(min_length=1, widget=HiddenInput)

    class Meta:
        model = Album
        fields = ['key', 'title', 'description', 'visibility']
        help_texts = {
            **description_help('album'),
            'title': ALBUM_TITLE_HELP,
        }
        widgets = {'visibility': VisibilityRadioSelect(
            attrs={'class': 'visibility-select'}), }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        super().clean()

        key = self.cleaned_data.get('key', '')
        title = self.cleaned_data.get('title', '')

        _check_admin_visibility(self)

        # If key is set to _new, generate a key from the title.
        if key != '_new':
            if key.startswith('_'):
                self.add_error(
                    'key',
                    ValidationError(
                        _('Keys starting with underscore are reserved for '
                          'system albums.'),
                        code='invalid'))
            return

        if title == '':
            self.add_error(
                'title',
                ValidationError(
                    _('This field is required.'),
                    code='required'))
            return

        key = slugify(title, lower=True, replace_leading_underscores=True)

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


def photo_label(photo: Photo):
    return mark_safe(
        f'''
<img
  alt="{photo.title}"
  src="/img/{photo.key}/sm"
  style="
    background: url(data:image/png;base64,{photo.tiny_base64});
    background-size: 100% 100%;
    font-size: 0;"
  height="{photo.thumbnail_height}"
  width="{photo.thumbnail_width}"
/>''')


class ModifyAlbumForm(ModelForm):
    class Meta:
        model = Album
        fields = ['title', 'description', 'cover_photo', 'visibility']
        help_texts = {
            **description_help('album'),
            'cover_photo': _(
                'Select a cover photo for the album. The cover photo is '
                'visible on the albums list page and in album preview image.'),
            'title': ALBUM_TITLE_HELP,
        }
        widgets = {
            'cover_photo': RadioSelect(
                attrs={
                    'class': 'photo-select'}),
            'visibility': VisibilityRadioSelect(
                attrs={
                    'class': 'visibility-select'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields['cover_photo'].queryset = Photo.objects.filter(
            album=self.instance)
        self.fields['cover_photo'].empty_label = None
        self.fields['cover_photo'].label_from_instance = photo_label

    def clean(self):
        super().clean()
        _check_admin_visibility(self)


class CreatePhotoForm(ModelForm):
    class Meta:
        model = Photo
        fields = [
            'key',
            'album',
            'title',
            'description',
            'timestamp',
            'height',
            'width',
            'tiny_base64',
            'camera_make',
            'camera_model',
            'lens_make',
            'lens_model',
            'focal_length',
            'f_number',
            'exposure_time',
            'iso_speed',
        ]
        error_messages = {
            'album': {
                'invalid_choice': _('Album with %(value)s key does not exist.')
            },
            'key': {
                'unique': _(
                    'Photo with this filename already exists in the album.'),
            },
        }


class ModifyPhotoForm(ModelForm):
    class Meta:
        model = Photo
        fields = ['title', 'description', 'alt_text']
        help_texts = {
            **description_help('photo'),
            'title': _(
                'Title for the photo. If not defined, the filename of the '
                'photo is used as the title.'
            ),
            'alt_text': ALT_TEXT_HELP,
        }


class CreatePhotoChangeRequestForm(ModelForm):
    class Meta:
        model = PhotoChangeRequest
        fields = ['photo', 'alt_text']


class ReviewPhotoChangeRequestForm(ModelForm):
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')], widget=None)

    class Meta:
        model = PhotoChangeRequest
        fields = ['alt_text']
        help_texts = {
            'alt_text': ALT_TEXT_HELP,
        }
