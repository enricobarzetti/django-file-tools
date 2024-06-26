from django.core.files.storage import default_storage
from rest_framework import fields
from rest_framework import serializers

from django_file_tools.s3 import bucket_exists
from django_file_tools.s3 import file_exists
from django_file_tools.s3 import files_exist_in_prefix


class FileField(fields.FileField):
    """Similar to the standard serializer FileField but takes strings as paths in the storage instead of file objects"""
    default_error_messages = fields.FileField.default_error_messages
    default_error_messages['does not exist'] = 'The file referenced does not exist'

    def get_storage(self):
        return default_storage

    def to_internal_value(self, data):
        storage = self.get_storage()
        if not storage.exists(data):
            self.fail('does not exist')
        return data


class FileFieldForModelSerializer(FileField):
    def get_storage(self):
        model = self.parent.Meta.model
        return getattr(model, self.field_name).field.storage


class S3PathField(fields.CharField):
    def to_internal_value(self, value):
        if value:
            value = value.replace('s3://', '')
            bucket_name, prefix = value.split('/', 1)
            if not bucket_exists(bucket_name):
                raise serializers.ValidationError(f'bucket {bucket_name} does not exist')

            if_file_exists = file_exists(bucket_name, prefix)
            if_folder_exists = files_exist_in_prefix(bucket_name, prefix)
            if (not if_file_exists) and (not if_folder_exists):
                if not prefix.endswith('/'):
                    raise serializers.ValidationError(f'{value} does not exist')
                else:
                    raise serializers.ValidationError(f'{value} has no files')
        return value
