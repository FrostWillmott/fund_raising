from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of an object to edit or delete it.
    The model instance must have either a 'created_by' or 'payer' attribute.
    """

    owner_field = 'created_by'  # Default field that identifies the owner

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Get the owner based on the specified field
        owner = getattr(obj, self.owner_field, None)

        # Write permissions are only allowed to the owner
        return owner == request.user


class IsCollectAuthorOrReadOnly(IsOwnerOrReadOnly):
    """Permission for Collect objects."""

    owner_field = 'created_by'


class IsPaymentPayerOrReadOnly(IsOwnerOrReadOnly):
    """Permission for Payment objects."""

    owner_field = 'payer'
