import datetime
import uuid

from django.conf import settings
from django.http.response import Http404
from django.http.response import JsonResponse

from django_file_tools.conf import app_settings
from django_file_tools.model_fields import TEMP_MARKER
from django_file_tools.s3 import EXPIRE_FAST
from django_file_tools.s3 import RETENTION
from django_file_tools.s3 import client


def create_presigned_post(bucket, key, tags=None, expiration=3600):
    if tags is None:
        tags = {}

    service = 's3'
    region = 'us-east-1'
    t = datetime.datetime.utcnow()
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = '/'.join([t.strftime('%Y%m%d'), region, service, 'aws4_request'])

    def get_tag_xml(tags):
        l = []
        for key, value in tags.items():
            s = f'<Tag><Key>{key}</Key><Value>{value}</Value></Tag>'
            l.append(s)
        return f'<Tagging><TagSet>{"".join(l)}</TagSet></Tagging>'

    conditions = [
        {'x-amz-algorithm': algorithm},
        {'x-amz-credential': credential_scope},
        {'x-amz-date': t.isoformat()},
        {'tagging': get_tag_xml(tags)},
        {'success_action_status': '201'},
        {'bucket': bucket},
        ['starts-with', '$key', TEMP_MARKER],
    ]

    fields = {
        'x-amz-algorithm': algorithm,
        'x-amz-credential': credential_scope,
        'x-amz-date': t.isoformat(),
        'tagging': get_tag_xml(tags),
        'success_action_status': '201',
    }

    return client.generate_presigned_post(
        bucket,
        key,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=expiration,
    )


def get_s3_signature(request):
    """Works with vue-dropzone"""
    name = request.GET.get('name')
    if name is None:
        raise Http404

    presigned = create_presigned_post(settings.AWS_STORAGE_BUCKET_NAME, name, {RETENTION: EXPIRE_FAST})

    return JsonResponse({
        'signature': presigned['fields'],
        'postEndpoint': presigned['url'],
    })


def get_s3_signature_temp(request):
    """Works with vue-dropzone"""
    name = request.GET.get('name')
    if name is None:
        raise Http404

    path = f'{app_settings.FILE_TOOLS_TEMP_FOLDER_PREFIX}-{uuid.uuid4()}/{name}'
    presigned = create_presigned_post(settings.AWS_STORAGE_BUCKET_NAME, path, {RETENTION: EXPIRE_FAST})

    return JsonResponse({
        'signature': presigned['fields'],
        'postEndpoint': presigned['url'],
    })
