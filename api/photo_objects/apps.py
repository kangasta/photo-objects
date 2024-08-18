from django.apps import AppConfig
from django.core.checks import Error, register
from django.conf import settings


class PhotoObjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'photo_objects'


@register()
def photo_objects_check(app_configs, **kwargs):
    errors = []

    try:
        conf = settings.PHOTO_OBJECTS_OBJSTO
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
        if not conf.get(key):
            errors.append(
                Error(
                    f'The PHOTO_OBJECTS_OBJSTO setting must define {key} '
                    'field.',
                    id='UNDEFINED_FIELD',
                    obj='photo_objects',
                ))

    return errors
