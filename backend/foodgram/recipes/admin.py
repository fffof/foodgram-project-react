from django.contrib import admin
from recipes import models

admin.site.register(models.teg)
admin.site.register(models.ingredients)
admin.site.register(models.recipe)
admin.site.register(models.Follow)
