from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag


class TagAdmin(admin.ModelAdmin):
    pass


class IngredientAdmin(admin.ModelAdmin):
    fields = ('name', 'measurement_unit',)
    list_filter = ('name',)


class FavoriteAdmin(admin.ModelAdmin):
    pass


class ShoppingCartAdmin(admin.ModelAdmin):
    pass


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(Tag, TagAdmin)
