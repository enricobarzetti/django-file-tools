from storages.backends.s3boto3 import S3Boto3Storage
from storages.utils import clean_name


class StorageCopyMixin:
    def copy(self, original, new_name, max_length=None, tags=None):
        new_name = self.get_available_name(new_name, max_length=max_length)
        return self._copy(original, new_name, tags)

    def copy_from_other_bucket(self, bucket_name, key, new_name, max_length=None, tags=None):
        new_name = self.get_available_name(new_name, max_length=max_length)
        return self._copy_from_other_bucket(bucket_name, key, new_name, tags)


class S3Storage(StorageCopyMixin, S3Boto3Storage):
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False

    @property
    def s3_client(self):
        return self.connection.meta.client

    def set_tags(self, key, tags):
        if tags is None:
            return

        tag_set = []
        for k, v in tags.items():
            tag_set.append({
                'Key': k,
                'Value': v,
            })
        self.s3_client.put_object_tagging(
            Bucket=self.bucket_name,
            Key=key,
            Tagging={
                'TagSet': tag_set
            }
        )

    def _copy(self, original, new_name, tags=None):
        normalized_original = self._normalize_name(clean_name(original))
        normalized_new_name = self._normalize_name(clean_name(new_name))
        copy_source = {
            'Bucket': self.bucket_name,
            'Key': normalized_original
        }
        self.bucket.copy(copy_source, normalized_new_name)
        self.set_tags(normalized_new_name, tags)
        return normalized_new_name

    def _copy_from_other_bucket(self, bucket_name, key, new_name, tags=None):
        normalized_new_name = self._normalize_name(clean_name(new_name))
        copy_source = {
            'Bucket': bucket_name,
            'Key': key
        }
        self.bucket.copy(copy_source, normalized_new_name)
        self.set_tags(normalized_new_name, tags)
        return normalized_new_name
