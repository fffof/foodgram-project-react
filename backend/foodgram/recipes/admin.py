from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag


class TagAdmin(admin.ModelAdmin):
    pass


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'id', 'author')
    readonly_fields = ('favorites',)
    fields = ('name', 'author', 'favorites',)
    list_filter = ('name', 'author', 'tag')

    def favorites(self, obj):
        return Favorite.objects.filter(recipe=obj.id).count()


class IngredientAdmin(admin.ModelAdmin):
    fields = ('name', 'measurement_unit',)
    list_filter = ('name',)


class FavoriteAdmin(admin.ModelAdmin):
    pass


class ShoppingCartAdmin(admin.ModelAdmin):
    pass


admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(Ingredient, IngredientAdmin) 
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin) 
admin.site.register(Tag, TagAdmin)