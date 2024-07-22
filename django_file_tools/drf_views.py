from django.conf import settings
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from django_file_tools.s3 import EXPIRE_FAST
from django_file_tools.s3 import RETENTION
from django_file_tools.views import create_presigned_post


class GetS3SignatureView(APIView):
    """Works with vue-dropzone"""
    def get(self, request, *args, **kwargs):
        name = request.query_params.get('name')
        if name is None:
            raise Http404

        presigned = create_presigned_post(settings.AWS_STORAGE_BUCKET_NAME, name, {RETENTION: EXPIRE_FAST})

        return Response({
            'signature': presigned['fields'],
            'postEndpoint': presigned['url'],
        })
