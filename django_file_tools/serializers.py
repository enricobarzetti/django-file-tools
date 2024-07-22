import copy

from django.db import models
from rest_framework import serializers

from django_file_tools import serializer_fields


class ModelSerializer(serializers.ModelSerializer):
    serializer_field_mapping = copy.deepcopy(serializers.ModelSerializer.serializer_field_mapping)
    serializer_field_mapping[models.FileField] = serializer_fields.FileFieldForModelSerializer
