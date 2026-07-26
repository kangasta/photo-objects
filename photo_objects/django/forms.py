from ciou.string import postfix_generator
from ciou.types import ensure_list

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

from .models import (
    Album,
    Photo,
    PhotoChangeRequest,
    PhotoReference,
    Story,
    Tag,
    Visibility,
    tag_input_validator,
)


ALT_TEXT_HELP = _('Alternative text content for the photo.')
TAGS_HELP = _(
    'Comma separated list of tags for the photo. Tags are used for '
    'organizing and searching photos.'
)
PHOTO_REF_TITLE_HELP = _(
    'Title for the photo in the selected story. If not defined, the title is '
    'inherited from the photo.'
)
PHOTO_REF_DESCRIPTION_HELP = _(
    'Description for the photo in the selected story. If not defined, the '
    'description is inherited from the photo.'
)


def collection_title_help(resource):
    return {'title': _(
        f'When creating a new {resource}, {resource} key is generated based '
        'on the title. Modifying the title later does not change the '
        f'{resource} key.'
    )}


def collection_cover_photo_help(resource):
    return {'cover_photo': _(
        f'Select a cover photo for the {resource}. The cover photo is '
        'visible on the list page and in the social media previews.'),
    }


def description_help(resource):
    return {'description': _(
        f'Optional description for the {resource}. If defined, the '
        f'description is visible on the {resource} details page. Use Markdown '
        'syntax to format the description.'),
    }


def visibility_help(visibility: str, resource: str):
    visibility = Visibility(visibility)
    if visibility == Visibility.PUBLIC:
        return _(
            f'The {resource} is visible to anyone without authentication.')
    if visibility == Visibility.HIDDEN:
        return _(
            f'The {resource} is visible to anyone with the link. Only '
            f'authenticated users can list the {resource}.')
    if visibility == Visibility.PRIVATE:
        return _(
            f'The {resource} is only visible to authenticated users.')
    if visibility == Visibility.ADMIN:
        return _(
            f'The {resource} is only visible to admin users.')
    return None


class VisibilityRadioSelect(RadioSelect):
    def __init__(self, resource, *args, **kwargs):
        self._resource = resource
        super().__init__(*args, **kwargs)

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
  <p class="helptext">
    {visibility_help(option.get('value'), self._resource)}
  </p>
</div>''')
        return option


def _check_admin_visibility(form):
    if form.user and form.user.is_staff:
        return

    if form.data.get("visibility") == Visibility.ADMIN:
        form.add_error(
            'visibility',
            ValidationError(
                _(
                    'Can not set admin visibility as non-admin user. Select a '
                    'different visibility setting.'),
                code='invalid'))
        return


class CreateCollectionForm(ModelForm):
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
                          'system resources.'),
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

        postfix_iter = postfix_generator()
        try:
            postfix = next(postfix_iter)
            # pylint: disable-next=no-member
            while self.Meta.model.objects.filter(key=key + postfix).exists():
                postfix = next(postfix_iter)
        except StopIteration:
            self.add_error(
                "title",
                ValidationError(
                    _('Could not generate unique key from the given title. '
                      'Try to use a different title for the resource.'),
                    code='unique'))
            return

        self.cleaned_data['key'] = key + postfix


class CreateAlbumForm(CreateCollectionForm):
    key = CharField(min_length=1, widget=HiddenInput)

    class Meta:
        model = Album
        fields = ['key', 'title', 'description', 'visibility']
        help_texts = {
            **description_help('album'),
            **collection_title_help('album'),
        }
        widgets = {'visibility': VisibilityRadioSelect(
            'album',
            attrs={'class': 'visibility-select'},
        )}


class CreateStoryForm(CreateCollectionForm):
    key = CharField(min_length=1, widget=HiddenInput)

    class Meta:
        model = Story
        fields = ['key', 'title', 'description', 'priority', 'visibility']
        help_texts = {
            **description_help('story'),
            **collection_title_help('story'),
        }
        widgets = {'visibility': VisibilityRadioSelect(
            'story',
            attrs={'class': 'visibility-select'},
        )}


def photo_label(photo: Photo | PhotoReference):
    title = photo.title
    if isinstance(photo, PhotoReference):
        photo = photo.photo

    return mark_safe(
        f'''
<img
  alt="{title}"
  src="/img/_uuid/{photo.uuid}/sm"
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
            **collection_cover_photo_help('album'),
            **collection_title_help('album'),
        }
        widgets = {
            'cover_photo': RadioSelect(
                attrs={'class': 'photo-select'},
            ),
            'visibility': VisibilityRadioSelect(
                'album',
                attrs={'class': 'visibility-select'},
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields['cover_photo'].queryset = self.instance.photo_set
        self.fields['cover_photo'].empty_label = None
        self.fields['cover_photo'].label_from_instance = photo_label

    def clean(self):
        super().clean()
        _check_admin_visibility(self)


class ModifyStoryForm(ModelForm):
    class Meta:
        model = Story
        fields = [
            'title',
            'description',
            'cover_photo',
            'visibility',
            'priority']
        help_texts = {
            **description_help('story'),
            **collection_cover_photo_help('story'),
            **collection_title_help('story'),
        }
        widgets = {
            'cover_photo': RadioSelect(
                attrs={'class': 'photo-select'},
            ),
            'visibility': VisibilityRadioSelect(
                'story',
                attrs={'class': 'visibility-select'},
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields['cover_photo'].queryset = self.instance.photo_references
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


def _tags_to_str(obj):
    if not obj:
        return obj

    tags = obj.get("tags", [])
    if not isinstance(tags, str):
        obj["tags"] = ", ".join(ensure_list(tags))

    return obj


def set_photo_tags(photo: Photo, raw_tags: str):
    tag_values = [t.strip() for t in raw_tags.split(",") if t.strip()]
    tags = []
    for value in tag_values:
        tag, _ = Tag.objects.get_or_create(value=value)
        tags.append(tag)
    photo.tags.set(tags)


class ModelFormWithTags(ModelForm):
    def __init__(self, data=None, initial=None, **kwargs):
        super().__init__(
            data=_tags_to_str(data),
            initial=_tags_to_str(initial),
            **kwargs,
        )


class ModifyPhotoForm(ModelFormWithTags):
    tags = CharField(
        label='Tags',
        required=False,
        help_text=TAGS_HELP,
        validators=[tag_input_validator])

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

    def clean(self):
        super().clean()

        raw_tags = self.cleaned_data.get("tags", "")
        set_photo_tags(self.instance, raw_tags)


class CreatePhotoReferenceForm(ModelForm):
    class Meta:
        model = PhotoReference
        fields = ['photo', 'story', 'title', 'description']
        help_texts = {
            'title': PHOTO_REF_TITLE_HELP,
            'description': PHOTO_REF_DESCRIPTION_HELP,
        }
        widgets = {'photo': HiddenInput()}

    def clean(self):
        super().clean()

        photo = self.cleaned_data.get('photo', '')
        story = self.cleaned_data.get('story', '')

        try:
            story.photo_references.get(photo=photo)
            self.add_error(
                'story',
                ValidationError(
                    _(
                        'The selected story already has reference to the '
                        'selected photo.',
                    ),
                    code='unique'))
        except PhotoReference.DoesNotExist:
            pass


class ModifyPhotoReferenceForm(ModelForm):
    class Meta:
        model = PhotoReference
        fields = ['title', 'description']
        help_texts = {
            'title': PHOTO_REF_TITLE_HELP,
            'description': PHOTO_REF_DESCRIPTION_HELP,
        }


class CreatePhotoChangeRequestForm(ModelFormWithTags):
    class Meta:
        model = PhotoChangeRequest
        fields = ['photo', 'alt_text', 'tags']


class ReviewPhotoChangeRequestForm(ModelFormWithTags):
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')], widget=None)

    class Meta:
        model = PhotoChangeRequest
        fields = ['alt_text', 'tags']
        help_texts = {
            'alt_text': ALT_TEXT_HELP,
            'tags': TAGS_HELP,
        }
