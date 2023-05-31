"""foodgram URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
