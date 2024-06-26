from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from django_file_tools.model_fields import copy_from_temp_storage
from django_file_tools.s3 import file_exists
from django_file_tools.s3 import get_client_resource
from django_file_tools.s3 import reset_bucket
from django_file_tools.storage_backends import S3Storage
from testapp.models import Something


class StorageTestCaseMixin:
    def setUp(self):
        client, resource = get_client_resource()
        try:
            client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        except ClientError:
            client.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        else:
            reset_bucket(settings.AWS_STORAGE_BUCKET_NAME)

    def tearDown(self):
        client, resource = get_client_resource()
        reset_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        client.delete_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)


class TestS3Storage(S3Storage):
    bucket_name = 'test-bucket'


class StorageTestCase(StorageTestCaseMixin, TestCase):
    def setUp(self):
        super().setUp()
        client, resource = get_client_resource()
        try:
            client.head_bucket(Bucket='test-bucket')
        except ClientError:
            client.create_bucket(Bucket='test-bucket')
        else:
            reset_bucket('test-bucket')

        # Save a file in the default bucket
        default_storage.save('temp/path/to/file', ContentFile(b''))

    def tearDown(self):
        super().tearDown()
        client, resource = get_client_resource()
        reset_bucket('test-bucket')
        client.delete_bucket(Bucket='test-bucket')

    def test_copy_file(self):
        storage = S3Storage()
        new_path = storage.copy('temp/path/to/file', 'file2')
        assert file_exists(settings.AWS_STORAGE_BUCKET_NAME, new_path)

    def test_copy_file_to_bucket(self):
        storage = TestS3Storage()
        new_path = storage.copy_from_other_bucket(settings.AWS_STORAGE_BUCKET_NAME, 'temp/path/to/file', 'file2')
        assert file_exists('test-bucket', new_path)


class ModelTestCase(StorageTestCaseMixin, TestCase):
    def test(self):
        s = Something.objects.create()
        s.content.save(name='thefile.txt', content=ContentFile(b''))
        assert file_exists(settings.AWS_STORAGE_BUCKET_NAME, f'something/{s.pk}/thefile.txt')


class SerializerTestCase(StorageTestCaseMixin, APITestCase):
    def test(self):
        default_storage.save('temp/path/to/file.mp4', ContentFile(b''))

        url = reverse('create')
        data = {'content': 'temp/path/to/file.mp4'}
        response = self.client.post(url, data, format='json')
        assert response.status_code == 201
        s = Something.objects.get()
        assert s.content.name == 'temp/path/to/file.mp4'

        copy_from_temp_storage(s)

        assert s.content.name == f'something/{s.pk}/file.mp4'
        assert file_exists(settings.AWS_STORAGE_BUCKET_NAME, f'something/{s.pk}/file.mp4')
