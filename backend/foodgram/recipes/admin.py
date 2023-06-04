from django.contrib import admin
from recipes import models

admin.site.register(models.Tag)
admin.site.register(models.Ingredients)
admin.site.register(models.Recipes)
admin.site.register(models.Follow)
