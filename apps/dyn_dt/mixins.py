from django.db import models
from django.contrib.auth.models import AnonymousUser
from .middleware import get_current_user  # already imported here

class UserTrackingMixin:
    """
    Mixin to automatically track the user who creates a model instance.
    """
    def save(self, *args, **kwargs):
        if not self.pk and not getattr(self, 'creado_por', None):  # Only on creation
            user = kwargs.pop('user', None)
            if not user:
                user = get_current_user()
            if user and not isinstance(user, AnonymousUser):
                self.creado_por = user

        super().save(*args, **kwargs)
