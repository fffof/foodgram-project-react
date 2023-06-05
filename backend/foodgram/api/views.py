from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django_filters import rest_framework
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Follow, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import AdminOrReadOnly, OwnerOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          ShoppingCartSerializer, SubscribeSerializer,
                          TagSerializer)

User = get_user_model()


class RecipeAnonymousFilters(rest_framework.FilterSet):

    tags = rest_framework.ModelMultipleChoiceFilter(
        field_name='tag__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )

    class Meta:
        model = Recipe
        fields = ('tags',)


class IngredientFilter(rest_framework.FilterSet):
    name = rest_framework.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name', 'measurement_unit')


class RecipeFilters(RecipeAnonymousFilters):

    is_favorited = rest_framework.BooleanFilter(
        field_name='favorites',
        method='get_filter_queryset',
        label='favorites',
    )
    is_in_shopping_cart = rest_framework.BooleanFilter(
        field_name='shoppings',
        method='get_filter_queryset',
        label='shopping cart',
    )
    author = rest_framework.NumberFilter(field_name='author__id')

    class Meta:
        model = RecipeAnonymousFilters.Meta.model
        fields = RecipeAnonymousFilters.Meta.fields + ('author',)

    def get_filter_queryset(self, queryset, field_name, value):
        user = self.request.user
        if not value:
            return queryset
        return queryset.filter(
            id__in=user.favorites.values_list('recipe')
            if field_name == 'favorites'
            else user.shoppings.values_list('recipe')
        )


class CustomPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 6


class CreateDeleteMixin:
    def add_del_obj_action(self, request, model, serializer, data):

        obj_exists = model.objects.filter(**data)
        if request.method == 'POST':
            serializer = serializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        obj_exists.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet, CreateDeleteMixin):
    pagination_class = CustomPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list' and not self.request.user.is_staff:
            return queryset.exclude(is_staff=True)
        return queryset

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        data = {
            'user': request.user.id,
            'author': id,
        }
        return self.add_del_obj_action(
            request,
            Follow,
            SubscribeSerializer,
            data,
        )

    @action(
        methods=('get',),
        url_path='me',
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def get_self_page(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        followers = self.paginate_queryset(request.user.followers.all())
        serializer = SubscribeSerializer(
            followers,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    permission_classes = (AdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (AdminOrReadOnly,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet, CreateDeleteMixin):
    queryset = Recipe.objects.all()
    permission_classes = (OwnerOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilters
    pagination_class = CustomPagination

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk):
        data = {
            'user': request.user.id,
            'recipe': pk
        }
        return self.add_del_obj_action(
            request,
            ShoppingCart,
            ShoppingCartSerializer,
            data,
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        if self.request.user.is_anonymous:
            self.filterset_class = RecipeAnonymousFilters
        return super().get_queryset()

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),

    )
    def download_shopping_cart(self, request):
        user = request.user
        text = 'Cписок покупок: \n'

        shopping_cart = IngredientRecipe.objects.filter(
            recipe_id__in=user.shoppings.values_list('recipe_id', flat=True)
        ).values_list(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(Sum('amount'))

        for index, ingredient in enumerate(sorted(shopping_cart), start=1):
            text += f'{index}. {ingredient[0].capitalize()} '
            text += f'({ingredient[1]}) - {ingredient[2]};\n'

        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )

        return response

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk):
        data = {
            'user': request.user.id,
            'recipe': pk,
        }
        return self.add_del_obj_action(
            request,
            Favorite,
            FavoriteSerializer,
            data,
        )
