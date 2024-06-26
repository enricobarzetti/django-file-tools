import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http.response import Http404
from django.http.response import JsonResponse

from django_file_tools.model_fields import TEMP_MARKER
from django_file_tools.s3 import EXPIRE_FAST
from django_file_tools.s3 import RETENTION
from django_file_tools.s3 import client


@login_required
def get_s3_signature(request):
    service = 's3'
    region = 'us-east-1'
    t = datetime.datetime.utcnow()
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = '/'.join([t.strftime('%Y%m%d'), region, service, 'aws4_request'])

    name = request.GET.get('name')
    if name is None:
        raise Http404

    def get_tag_xml(key, value):
        return f"<Tagging><TagSet><Tag><Key>{key}</Key><Value>{value}</Value></Tag></TagSet></Tagging>"

    conditions = [
        {"x-amz-algorithm": algorithm},
        {"x-amz-credential": credential_scope},
        {"x-amz-date": t.isoformat()},
        {"tagging": get_tag_xml(RETENTION, EXPIRE_FAST)},
        {"success_action_status": "201"},
        {"bucket": settings.AWS_STORAGE_BUCKET_NAME},
        ["starts-with", "$key", TEMP_MARKER],
    ]

    fields = {
        "x-amz-algorithm": algorithm,
        "x-amz-credential": credential_scope,
        "x-amz-date": t.isoformat(),
        "tagging": get_tag_xml(RETENTION, EXPIRE_FAST),
        "success_action_status": "201",
    }

    presigned = client.generate_presigned_post(
        settings.AWS_STORAGE_BUCKET_NAME,
        name,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=7*24*60,
    )

    return JsonResponse({
        'signature': presigned['fields'],
        'postEndpoint': presigned['url'],
    })
