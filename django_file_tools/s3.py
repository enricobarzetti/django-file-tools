import errno
import os
import posixpath
from datetime import date
from pathlib import PurePath

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

from django_file_tools.constants import TEMP_MARKER

RETENTION = 'retention'
EXPIRE_FAST = 'expire_fast'
EXPIRE_SLOW = 'expire_slow'


def get_client_resource():
    client = boto3.client(
        service_name='s3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    )
    resource = boto3.resource(
        service_name='s3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    )
    return client, resource


client, resource = get_client_resource()


def reset_bucket(bucket):
    bucket = resource.Bucket(bucket)
    bucket.objects.all().delete()


def bucket_exists(bucket_name):
    try:
        client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError:
        return False

def assert_dir_exists(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def download_dir(bucket, path, target):
    # Handle missing / at end of prefix
    if not path.endswith('/'):
        path += '/'

    paginator = client.get_paginator('list_objects_v2')
    for result in paginator.paginate(Bucket=bucket, Prefix=path):
        # Download each file individually
        for key in result['Contents']:
            # Calculate relative path
            rel_path = key['Key'][len(path):]
            # Skip paths ending in /
            if not key['Key'].endswith('/'):
                local_file_path = os.path.join(target, rel_path)
                # Make sure directories exist
                local_file_dir = os.path.dirname(local_file_path)
                assert_dir_exists(local_file_dir)
                client.download_file(bucket, key['Key'], local_file_path)


def path_is_file_or_directory(bucket, path):
    paginator = client.get_paginator('list_objects_v2')
    total = 0
    for result in paginator.paginate(Bucket=bucket, Prefix=path):
        total += result['KeyCount']

    if not path.endswith('/'):
        path += '/'
    total_with_slash = 0
    for result in paginator.paginate(Bucket=bucket, Prefix=path):
        total_with_slash += result['KeyCount']
    if total == total_with_slash and total > 1:
        return 'directory'
    else:
        return 'file'


def download(bucket, path, target):
    is_directory = path_is_file_or_directory(bucket, path) == 'directory'
    if is_directory:
        download_dir(bucket, path, target)
        return (target, is_directory)
    else:
        assert_dir_exists(target)
        filename = os.path.split(path)[1]
        target_path = f'{target}/{filename}'
        client.download_file(bucket, path, target_path)
        return (target_path, is_directory)


def normalize_prefix(prefix):
    # The prefix needs to end with a slash, but if the root is empty, leave
    # it.
    if prefix and not prefix.endswith('/'):
        prefix += '/'
    return prefix


def get_files_under_prefix(bucket_name, prefix):
    def ls(bucket_name, prefix):
        # Use a hash lookup instead of an array to prevent duplicate directories
        directories = {}
        files = []
        paginator = client.get_paginator('list_objects')
        pages = paginator.paginate(Bucket=bucket_name, Delimiter='/', Prefix=prefix)
        for page in pages:
            for entry in page.get('CommonPrefixes', ()):
                key = posixpath.relpath(entry['Prefix'], prefix)
                if not key in directories:
                    directories[key] = True
            for entry in page.get('Contents', ()):
                files.append(posixpath.relpath(entry['Key'], prefix))
        return directories.keys(), files

    def collect_files(bucket_name, prefix, ret):
        prefix = normalize_prefix(prefix)

        directories, files = ls(bucket_name, prefix)
        for file_ in files:
            # S3 files named . are special files that are created when the "Create Folder" button is used on S3.  They
            # show up when calling list_objects(), but will fail when head_object() is called on them.
            if file_ == '.':
                continue
            ret.append(f'{prefix}{file_}')
        for directory in directories:
            ret = collect_files(bucket_name, f'{prefix}{directory}', ret)
        return ret

    return collect_files(bucket_name, prefix, [])


def files_exist_in_prefix(bucket_name, prefix):
    prefix = normalize_prefix(prefix)
    paginator = client.get_paginator('list_objects')
    pages = paginator.paginate(Bucket=bucket_name, Delimiter='/', Prefix=prefix)
    page = next(iter(pages))
    if 'Contents' in page:
        return True
    return False


def file_exists(bucket_name, key):
    try:
        client.get_object(Bucket=bucket_name, Key=key)
    except ClientError as ex:
        if ex.response['Error']['Code'] == 'NoSuchKey':
            return False
        else:
            raise
    else:
        return True


def get_file_without_prefix(file_, prefix):
    if prefix:
        prefix = normalize_prefix(prefix)
        return file_.split(prefix)[-1]
    else:
        return file_


def get_s3_path(path):
    path = PurePath(settings.AWS_STORAGE_BUCKET_NAME) / PurePath(path)
    return f's3://{path}'


def s3_read(key):
    s3_object = client.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)
    body = s3_object['Body']
    return body.read()


def s3_write(key, content):
    client.put_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key, Body=content)


def s3_delete(key):
    client.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key)


def set_tags(key, tags):
    if tags is None:
        return

    tag_set = []
    for k, v in tags.items():
        tag_set.append({
            'Key': k,
            'Value': v,
        })
    client.put_object_tagging(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=key,
        Tagging={
            'TagSet': tag_set
        }
    )


def s3_temp_folder_cleanup():
    def dir(bucket_name, prefix):
        # Use a hash lookup instead of an array to prevent duplicate directories
        directories = {}
        paginator = client.get_paginator('list_objects')
        pages = paginator.paginate(Bucket=bucket_name, Delimiter='/', Prefix=prefix)
        for page in pages:
            for entry in page.get('CommonPrefixes', ()):
                key = posixpath.relpath(entry['Prefix'], prefix)
                if not key in directories:
                    directories[key] = True
        return directories.keys()

    delete_set = dict(Objects=[])
    for prefix in dir(bucket_name=settings.AWS_STORAGE_BUCKET_NAME, prefix=TEMP_MARKER):
        response = client.list_objects(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=prefix, MaxKeys=1)
        for entry in response.get('Contents', ()):
            diff_in_hours = (date.today() - entry['LastModified']).total_seconds() / 3600
            # If the first file in the folder (prefix) is over a day old, delete the whole folder
            if diff_in_hours >= 24:
                delete_set['Objects'].append(dict(Key=entry['Key']))
                if len(delete_set['Objects']) >= 1000:
                    client.delete_objects(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Delete=delete_set)
                    delete_set = dict(Objects=[])
            break
    if len(delete_set['Objects']) > 0:
        client.delete_objects(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Delete=delete_set)


def s3_lifecycle_configuration():
    client.put_bucket_lifecycle_configuration(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        LifecycleConfiguration={
            'Rules': [
                {
                    'ID': 'Expire fast',
                    'Filter': {
                        'Tag': {
                            'Key': RETENTION,
                            'Value': EXPIRE_FAST,
                        },
                    },
                    'Status': 'Enabled',
                    'Expiration': {
                        'Days': 1,
                    },
                },
                {
                    'ID': 'Expire slow',
                    'Filter': {
                        'Tag': {
                            'Key': RETENTION,
                            'Value': EXPIRE_SLOW,
                        },
                    },
                    'Status': 'Enabled',
                    'Expiration': {
                        'Days': 180,
                    },
                },
            ]
        }
    )
