from django.conf import settings
from django.test.runner import DiscoverRunner

TEST_BUCKET_PREFIX = 'test-'


class Runner(DiscoverRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        settings.AWS_STORAGE_BUCKET_NAME = TEST_BUCKET_PREFIX + settings.AWS_STORAGE_BUCKET_NAME
