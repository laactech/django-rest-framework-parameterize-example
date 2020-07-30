from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):
    # First Name and Last Name do not cover name patterns around the globe.
    name = models.CharField(_("Name"), max_length=254)

    def __str__(self):
        return f"{self.name} {self.email}"
