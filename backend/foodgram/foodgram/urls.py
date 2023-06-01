from api.views import (ConfirmationView, FavoriteViewSet, RecipesViewSet,
                       SignupView, UserFollowingViewSet, UserFollowViewSet,
                       UserViewSet)
from django.contrib import admin
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
v1_router.register(r"recipes", RecipesViewSet, basename="recipe")
urlpatterns = [
    path('admin/', admin.site.urls),
    path("users/subscriptions/", UserFollowViewSet.as_view({'get': 'list'})),
    path("users/", SignupView.as_view()),
    path('api/auth/token/login/', ConfirmationView.as_view()),
    path('', include(v1_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
