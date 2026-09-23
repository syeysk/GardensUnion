from rest_framework import serializers


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

    # def create(self, validated_data):
    #     return self.Meta.model.objects.create(**validated_data)
