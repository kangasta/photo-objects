from django.contrib import admin

from .models import Album, Photo, PhotoChangeRequest, SiteSettings

admin.site.register(Album)
admin.site.register(Photo)
admin.site.register(SiteSettings)
admin.site.register(PhotoChangeRequest)
