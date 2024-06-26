from django_file_tools.serializers import ModelSerializer
from testapp.models import Something


class SomethingSerializer(ModelSerializer):
    class Meta:
        model = Something
        fields = ['content']
