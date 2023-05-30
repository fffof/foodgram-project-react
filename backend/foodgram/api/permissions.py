from rest_framework.permissions import (SAFE_METHODS, BasePermission,
                                        IsAdminUser)


class IsSuperUser(IsAdminUser):
    """Доступ пользователя с правами не ниже Администратора."""

    def has_permission(self, request, view):
        return request.user.is_superuser