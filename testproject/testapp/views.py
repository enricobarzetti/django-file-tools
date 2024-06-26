from rest_framework.generics import UpdateAPIView
from rest_framework.generics import CreateAPIView

from testapp.models import Something
from testapp.serializers import SomethingSerializer


class SomethingUpdateView(UpdateAPIView):
    queryset = Something.objects.all()
    serializer_class = SomethingSerializer


class SomethingCreateView(CreateAPIView):
    queryset = Something.objects.all()
    serializer_class = SomethingSerializer
