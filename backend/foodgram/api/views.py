
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from recipes.models import (Favorite, Follow, ShoppingCart, recipe,
                            recipe_ingredients)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from . import serializers

User = get_user_model()


# Create your views here.
class SignupView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        if User.objects.filter(username=username).exists():
            if User.objects.get(username=username).email != email:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            return Response(status=status.HTTP_200_OK)
        serializer = serializers.SignupSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ConfirmationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        password = request.data.get('password')
        email = request.data.get('email')
        serializer = serializers.ConfirmationCodeSerializer(
            data=self.request.data
        )
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, email=email)
        if user.password == password:
            token = AccessToken.for_user(user)
            return Response(
                {'token': str(token)}, status=status.HTTP_200_OK
            )
        return Response(
            {'confirmation_code': 'confirmation_code is uncorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.CustomUserSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (SearchFilter,)
    search_fields = ('id',)
    lookup_field = 'id'
    http_method_names = ['patch', 'get', 'post', 'delete']

    @action(
        methods=['get', 'patch'],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        if request.method == 'GET':
            serializer = serializers.CustomUserSerializer(self.request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        user = get_object_or_404(User, username=self.request.user)
        serializer = serializers.CustomUserSerializer(
            user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        methods=['post', ],
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        new_password = request.data.get("new_password")
        current_password = request.data.get("current_password")
        username = request.user.username
        serializer = serializers.SetPasswordSerializer(
            data=self.request.data
        )
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(User, username=username)
        if user.password == current_password:
            return Response(
                {'new current password': str(new_password)},
                status=status.HTTP_200_OK
            )
        return Response(
            {'you took mistake': 'current password is another'},
            status=status.HTTP_400_BAD_REQUEST
        )


def add_del_obj_action(request, model, serializer, data):
    """Функция для добавления и удаления данных в модели Favorite,
    Follow, ShoppingCart."""

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


class RecipesViewSet(viewsets.ModelViewSet):
    queryset = recipe.objects.all()
    serializer_class = serializers.CustomRecipeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (SearchFilter,)
    search_fields = ('id',)
    lookup_field = ('id')
    http_method_names = ['patch', 'get', 'post', 'delete']

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        print(request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, id):
        data = {
            'user': request.user.id,
            'recipe': id,
        }
        return add_del_obj_action(
            request,
            Favorite,
            serializers.FavoriteSerializer,
            data,
        )

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def shopping_card(self, request, id):
        data = {
            'user': request.user.id,
            'recipe': id,
        }
        return add_del_obj_action(
            request,
            ShoppingCart,
            serializers.ShoppingCartSerializer,
            data,
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=(IsAuthenticated,),

    )
    def download_shopping_cart(self, request):
        user = request.user
        text = 'Cписок покупок: \n'
        shopping_cart = recipe_ingredients.objects.filter(
            recipe_id__in=user.shoppings.values_list('recipe_id', flat=True)
        ).values_list(
            'ingredients__title', 'ingredients__measurement'
        ).annotate(Sum('amount'))

        for index, ingredient in enumerate(sorted(shopping_cart), start=1):
            text += f'{index}. {ingredient[0].capitalize()} ' \
                    f'({ingredient[1]}) - {ingredient[2]};\n'

        response = HttpResponse(text, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )

        return response


class UserFollowingViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
    serializer_class = serializers.CustomFollowSerializer
    permission_classes = (IsAuthenticated,)

    def get_subscriber_id(self):
        return get_object_or_404(User, id=self.kwargs.get("user_id"))

    def perform_create(self, serializer):
        author = self.request.user
        subscriber = self.get_subscriber_id()
        serializer.save(author=author, subscriber=subscriber)


class UserFollowViewSet(viewsets.ViewSet):
    def list(self, request):
        followers = request.user.follower.all()
        serializer = serializers.UserFollowGettingSerializer(
            followers,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)


class FavoriteViewSet(viewsets.ViewSet):
    queryset = recipe()
    serializer_class = serializers.CustomRecipSerializer
    permission_classes = (IsAuthenticated,)

    def get_recipe_id(self):
        return get_object_or_404(recipe, id=self.kwargs.get("recipe_id"))

    def perform_create(self, serializer):
        user = self.request.user
        recip = self.get_recip_id()
        serializer.save(user=user, recipe=recip)
