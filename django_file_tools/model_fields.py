from pathlib import PurePath

from django.db.models.fields import files

from django_file_tools.constants import TEMP_MARKER
from django_file_tools.s3 import get_file_without_prefix


class FieldFile(files.FieldFile):
    def copy(self, original, save=True, tags=None):
        path = PurePath(original)
        new_name = path.parts[-1]
        new_name = self.field.generate_filename(self.instance, new_name)
        self.name = self.storage.copy(original, new_name, max_length=self.field.max_length, tags=tags)
        setattr(self.instance, self.field.name, self.name)

        # Save the object because it has changed, unless save is False
        if save:
            self.instance.save()

    def copy_from_other_bucket(self, bucket_name, key, prefix=None, save=True, tags=None):
        new_name = get_file_without_prefix(key, prefix)
        new_name = self.field.generate_filename(self.instance, new_name)
        self.name = self.storage.copy_from_other_bucket(bucket_name, key, new_name, max_length=self.field.max_length, tags=tags)
        setattr(self.instance, self.field.name, self.name)

        # Save the object because it has changed, unless save is False
        if save:
            self.instance.save()

    def replace(self, save=True, tags=None):
        original = self.name
        self.copy(original, save, tags)
        self.storage.delete(original)

    @property
    def url(self):
        self._require_file()
        method_name = f'get_{self.field.name}_filename'
        parameters = None
        if hasattr(self.instance, method_name):
            filename = getattr(self.instance, method_name)()
            filename = self.storage.generate_filename(filename)
            parameters = {'ResponseContentDisposition': f'attachment; filename={filename}'}
        return self.storage.url(self.name, parameters=parameters)


class FileField(files.FileField):
    attr_class = FieldFile


def copy_from_temp_storage(instance, tags=None):
    # If tags is not passed then clear them
    if tags is None:
        tags = {}

    save = False
    for field in instance._meta.fields:
        if isinstance(field, FileField):
            file = getattr(instance, field.name)
            if file.name != '':
                if PurePath(file.name).parts[0].startswith(TEMP_MARKER):
                    file.replace(save=False, tags=tags)
                    save = True
    if save:
        instance.save()
