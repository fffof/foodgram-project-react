import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from recipes.models import (Favorite, Follow, ShoppingCart, ingredients,
                            recipe, recipe_ingredients, teg)
from rest_framework import serializers

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email',
            'username',
            "first_name",
            "last_name",
            "password")

    def validate(self, data):
        if data['username'] == 'me':
            raise serializers.ValidationError('Нельзя использовать имя me')
        return data


class ConfirmationCodeSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=150)
    password = serializers.CharField()


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'username', 'first_name',
            'last_name', 'email', "id"
        )
        lookup_field = 'username'


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):

        if isinstance(data, str) and data.startswith('data:image'):

            format, imgstr = data.split(';base64,')

            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = ingredients
        fields = ("id",)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=ingredients.objects.all(),
        source='ingredients.id'
    )
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement = serializers.ReadOnlyField(
        source='ingredients.measurement'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = recipe_ingredients
        fields = ('id', 'name', 'measurement', 'amount')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = teg
        fields = ('id', 'name', 'color', 'slug')


class RecipeViewSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField(
        read_only=True,
        source='get_ingredients'
    )

    class Meta:
        model = recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'coocking_time'
        )

    def get_ingredients(self, obj):
        ingredients = recipe_ingredients.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data


class CustomRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    coocking_time = serializers.CharField()

    class Meta:
        model = recipe
        fields = (
            "id",
            "tags",
            "ingredients",
            "name",
            "image",
            "text",
            "coocking_time",
            "author"
        )

    def create(self, validated_data):
        tags = validated_data.pop("tags")

        if 'ingredients' not in self.initial_data:

            recip = recipe.objects.create(**validated_data)
            return recip
        ingredientics = validated_data.pop('ingredients')

        recip = recipe.objects.create(**validated_data)
        obj_ingredient_recipe = []

        for ingredient in ingredientics:
            print(ingredient['ingredients'].get("id"))
            obj_ingredient_recipe.append(
                recipe_ingredients(
                    recipe=recip,
                    ingredients=ingredient['ingredients'].get("id"),
                    amount=ingredient.get('amount'),
                )
            )
        recipe_ingredients.objects.bulk_create(obj_ingredient_recipe)

        recip.tags.set(tags)
        return recip

    def to_representation(self, instance):
        return RecipeViewSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class CustomFollowSerializer(serializers.ModelSerializer):
    id = serializers.SlugField(source="follower", read_only=True)

    class Meta:
        model = Follow
        fields = ("id",)


class CustomRecipSerializer(serializers.ModelSerializer):
    id = serializers.SlugField(source="author", read_only=True)

    class Meta:
        models = recipe
        fileds = ("id",)


class UserFollowGettingSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.ReadOnlyField(source="author.id")
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")

    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "recipes",
            "recipes_count",
            "is_subscribed")

    def get_recipes(self, obj):
        queryset = recipe.objects.filter(author=obj.author)
        serializer = CustomRecipeSerializer(
            queryset,
            many=True,
            context={'request': self.context.get('request')},
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return recipe.objects.filter(author=obj.author).count()

    def get_is_subscribed(self, obj):
        return True


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(
        use_url=True,
        allow_null=True,
        required=False,
        source='recipe.image',
    )
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = ('user', 'recipe', 'id', 'name', 'image', 'cooking_time')
        extra_kwargs = {
            'user': {'write_only': True},
            'recipe': {'write_only': True},
            'image': {'read_only': True},
        }

    def validate(self, data):
        obj_exists = self.Meta.model.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists()
        if not obj_exists:
            return data
        model_name = (
            'избранное' if self.Meta.model == Favorite
            else 'список покупок'
        )
        raise serializers.ValidationError(
            f'Рецепт уже добавлен в {model_name}'
        )


class FavoriteSerializer(FavoriteShoppingCartSerializer):
    pass


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.ImageField(
        use_url=True,
        allow_null=True,
        required=False,
        source='recipe.image',
    )
    coocking_time = serializers.ReadOnlyField(source='recipe.coocking_time')

    class Meta:
        model = Favorite
        fields = ('user', 'recipe', 'id', 'name', 'image', 'coocking_time')
        extra_kwargs = {
            'user': {'write_only': True},
            'recipe': {'write_only': True},
            'image': {'read_only': True},
        }


class ShoppingCartSerializer(FavoriteShoppingCartSerializer):

    class Meta:
        model = ShoppingCart
        fields = FavoriteShoppingCartSerializer.Meta.fields
        extra_kwargs = FavoriteShoppingCartSerializer.Meta.extra_kwargs
