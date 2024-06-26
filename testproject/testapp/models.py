from django.db import models

from django_file_tools.model_fields import FileField


def name(instance, filename):
    return f'something/{instance.pk}/{filename}'


class Something(models.Model):
    content = FileField(upload_to=name)
