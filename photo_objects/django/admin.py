from django.contrib import admin

from .models import Album, Photo, SiteSettings

admin.site.register(Album)
admin.site.register(Photo)
admin.site.register(SiteSettings)
