from django.core.exceptions import FieldDoesNotExist 
from rest_framework import serializers

from gardensunion.base.models import Tag


class EntityUpdateSerializer(serializers.ModelSerializer):
    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.Meta.model = model
        try:
            model._meta.get_field('tags')
            self.Meta.exclude = ['tags']
        except FieldDoesNotExist:
            self.Meta.fields = '__all__'

    class Meta:
        model = None


class EntityCreateSerializer(serializers.ModelSerializer):
    def __init__(self, model, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.Meta.model = model
        try:
            model._meta.get_field('tags')
            self.Meta.exclude = ['tags']
        except FieldDoesNotExist:
            self.Meta.fields = '__all__'

    class Meta:
        model = None
        


class TagEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class TagCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name', 'parent']
