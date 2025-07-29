from django.db import models
from django.contrib.auth.models import AnonymousUser
from .middleware import get_current_user  # already imported here

from django.db import models
from django.contrib.auth.models import AnonymousUser
from .middleware import get_current_user  # ya importado

class UserTrackingMixin:
    """
    Mixin para registrar automáticamente el usuario que crea y modifica una instancia.
    """
    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if not user:
            user = get_current_user()
        if user and not isinstance(user, AnonymousUser):
            if not self.pk and hasattr(self, 'creado_por') and not getattr(self, 'creado_por', None):
                self.creado_por = user
            if hasattr(self, 'modificado_por'):
                self.modificado_por = user
        super().save(*args, **kwargs)
