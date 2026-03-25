from rest_framework.permissions import BasePermission

from .models import UserProfile


class IsApprovedUser(BasePermission):
    """Allow access only to authenticated users whose account has been approved."""

    message = '您的账号尚未获得访问权限。'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        # Superusers bypass the profile check
        if request.user.is_superuser:
            return True
        try:
            return request.user.profile.status == UserProfile.STATUS_APPROVED
        except UserProfile.DoesNotExist:
            return False
