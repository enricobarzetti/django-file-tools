from botocore.exceptions import ClientError
from django.conf import settings

from django_file_tools.s3 import get_client_resource
from django_file_tools.s3 import reset_bucket


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
