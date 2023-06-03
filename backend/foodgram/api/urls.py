from api.views import (ConfirmationView, FavoriteViewSet, RecipesViewSet,
                       TagViewSet, UserFollowingViewSet, UserFollowViewSet,
                       UserViewSet)
from django.urls import include, path
from rest_framework.routers import DefaultRouter

v1_router = DefaultRouter()

v1_router.register('users', UserViewSet, basename='user')
v1_router.register(
    r'users/(?P<user_id>\d+)/subscribe',
    UserFollowingViewSet,
    basename='subscription'
)
v1_router.register(
    r'recipes/(?P<recipe_id>\d+)/favorite',
    FavoriteViewSet,
    basename='subscription'
)
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register(r"recipes", RecipesViewSet, basename="recipe")
urlpatterns = [
    path("users/subscriptions/", UserFollowViewSet.as_view({'get': 'list'})),
    path('auth/token/login/', ConfirmationView.as_view()),
    path('', include(v1_router.urls)),
]
