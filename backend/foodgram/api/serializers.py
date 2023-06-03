from django.contrib.auth import get_user_model
from recipes.models import (Favorite, Follow, Ingredients, Recipes,
                            Recipes_Ingredients, ShoppingCart, Tag)
from rest_framework import serializers

from .fields import Base64ImageField

User = get_user_model()


class GetFiledMixin:
    def get_is_field_action(self, request, model, data):
        """Функция для фильтрации queryset по заданным параметрам."""

        user = None
        if request and hasattr(request, 'user'):
            user = request.user
        if not user:
            return False
        data.update({'user': user.id})
        return model.objects.filter(**data).exists()


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


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ("id",)


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(),
        source='ingredients.id'
    )
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )
    amount = serializers.IntegerField()

    class Meta:
        model = Recipes_Ingredients
        fields = ('id', 'name', 'measurement', 'amount')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeViewSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True)
    ingredients = serializers.SerializerMethodField(
        read_only=True,
        source='get_ingredients'
    )

    class Meta:
        model = Recipes
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
        ingredients = Recipes_Ingredients.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients, many=True).data


class CustomRecipeSerializer(serializers.ModelSerializer, GetFiledMixin):
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    coocking_time = serializers.CharField()
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipes
        fields = (
            "id",
            "tags",
            "ingredients",
            'is_favorited',
            'is_in_shopping_cart',
            "name",
            "image",
            "text",
            "coocking_time",
            "author"
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        data = {
            'recipe': obj.id
        }
        return self.get_is_field_action(request, Favorite, data)

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        data = {
            'recipe': obj.id
        }
        return self.get_is_field_action(request, ShoppingCart, data)

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        if 'ingredients' not in self.initial_data:
            return Recipes.objects.create(**validated_data)
        ingredientics = validated_data.pop('ingredients')
        recip = Recipes.objects.create(**validated_data)
        Recipes_Ingredients.objects.bulk_create(
            [Recipes_Ingredients(
                recipe=recip,
                ingredients=ingredient['ingredients'].get("id"),
                amount=ingredient.get('amount'),
            ) for ingredient in ingredientics])

        recip.tags.set(tags)
        return recip

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags")
        if 'ingredients' not in self.initial_data:
            return Recipes.objects.create(**validated_data)
        ingredientics = validated_data.pop('ingredients')
        recip = Recipes.objects.create(**validated_data)
        Recipes_Ingredients.objects.bulk_create(
            [Recipes_Ingredients(
                recipe=recip,
                ingredients=ingredient['ingredients'].get("id"),
                amount=ingredient.get('amount'),
            ) for ingredient in ingredientics])

        recip.tags.set(tags)
        return recip

        return super().update(instance, validated_data)

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
        models = Recipes
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
        queryset = Recipes.objects.filter(author=obj.author)
        serializer = CustomRecipeSerializer(
            queryset,
            many=True,
            context={'request': self.context.get('request')},
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipes.objects.filter(author=obj.author).count()

    def get_is_subscribed(self, obj):
        return True


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class FavoriteShoppingCartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='Recipes.id')
    name = serializers.ReadOnlyField(source='Recipes.name')
    image = serializers.ImageField(
        use_url=True,
        allow_null=True,
        required=False,
        source='Recipes.image',
    )
    cooking_time = serializers.ReadOnlyField(source='Recipes.cooking_time')

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
    id = serializers.ReadOnlyField(source='Recipes.id')
    name = serializers.ReadOnlyField(source='Recipes.name')
    image = serializers.ImageField(
        use_url=True,
        allow_null=True,
        required=False,
        source='Recipes.image',
    )
    coocking_time = serializers.ReadOnlyField(source='Recipes.coocking_time')

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
