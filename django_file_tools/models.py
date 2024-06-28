from django.db import models

from django_file_tools.model_fields import copy_from_temp_storage


class FileStorageModel(models.Model):
    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)
        copy_from_temp_storage(self)
