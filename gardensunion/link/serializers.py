from rest_framework import serializers
from rest_framework import serializers
from gardensunion.link.models import Link


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = '__all__'