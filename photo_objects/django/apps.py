from django.apps import AppConfig
from django.core.checks import Error, register
from django.conf import settings

from photo_objects.django.conf import validate_photo_sizes


class PhotoObjects(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'photo_objects.django'
    label = 'photo_objects'

    def ready(self):
        from . import signals


@register()
def photo_objects_check(app_configs, **kwargs):
    errors = []

    try:
        objsto_conf = settings.PHOTO_OBJECTS_OBJSTO
    except AttributeError:
        errors.append(
            Error(
                'The PHOTO_OBJECTS_OBJSTO setting must be defined.',
                id='UNDEFINED_SETTING',
                obj='photo_objects',
            )
        )
        return errors

    for key in ('URL', 'ACCESS_KEY', 'SECRET_KEY',):
        if not objsto_conf.get(key):
            errors.append(
                Error(
                    f'The PHOTO_OBJECTS_OBJSTO setting must define {key} '
                    'field.',
                    id='UNDEFINED_FIELD',
                    obj='photo_objects',
                ))

    try:
        sizes_conf = settings.PHOTO_OBJECTS_PHOTO_SIZES
        errors.extend(
            validate_photo_sizes(
                sizes_conf,
                'The PHOTO_OBJECTS_PHOTO_SIZES'))
    except AttributeError:
        # Use default values if sizes are not configured
        pass

    return errors
