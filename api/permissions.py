from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit or delete it.
    The model instance must have either a 'created_by' or 'payer' attribute.
    """

    owner_field = 'created_by'

    def has_object_permission(self, request: Request, view: ViewSet, obj: Any):
        if request.method in permissions.SAFE_METHODS:
            return True

        owner = getattr(obj, self.owner_field, None)

        return owner == request.user


class IsCollectAuthorOrReadOnly(IsOwnerOrReadOnly):
    """Permission for Collect objects."""

    owner_field = 'created_by'


class IsPaymentPayerOrReadOnly(IsOwnerOrReadOnly):
    """Permission for Payment objects."""

    owner_field = 'payer'
