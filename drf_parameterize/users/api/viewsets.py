from rest_framework import viewsets

from .. import models
from . import serializers


class UserViewset(viewsets.ReadOnlyModelViewSet):
    serializer_class = serializers.UserHyperlinkedModelSerializer

    def get_queryset(self):
        return models.User.objects.all()
