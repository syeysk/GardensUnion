from rest_framework import serializers

from gardensunion.base.models import Tag


class EntityUpdateSerializer(serializers.ModelSerializer):
    def __init__(self, model, fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.Meta.model = model
        self.Meta.fields = fields

    class Meta:
        model = None
        fields = []


class EntityCreateSerializer(serializers.ModelSerializer):
    def __init__(self, model, fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.Meta.model = model
        self.Meta.fields = fields

    class Meta:
        model = None
        fields = []


class TagEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class TagCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name', 'parent']
