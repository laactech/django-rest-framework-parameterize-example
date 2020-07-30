import secrets

import factory

from . import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.User

    name = factory.Faker("name")
    email = factory.Sequence(lambda n: f"user-{n}{secrets.token_urlsafe(5)}@example.com")

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not isinstance(self, dict):
            self.set_password(secrets.token_urlsafe())

    @factory.post_generation
    def username(self, create, extracted, **kwargs):
        if not isinstance(self, dict):
            self.username = secrets.token_urlsafe()
