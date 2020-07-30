from rest_framework import serializers

from .. import models


class UserHyperlinkedModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.User
        fields = ("name", "email", "url")
