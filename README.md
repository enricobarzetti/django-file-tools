Run MinIO:

`MINIO_ROOT_USER=admin MINIO_ROOT_PASSWORD=password ./minio server temp --address ":9000" --console-address ":9001"`

Go to the MinIO console and generate access keys.  Set values in .env:

```
MINIO_ENDPOINT=http://127.0.0.1:9000
MINIO_ACCESS_KEY=value
MINIO_SECRET_ACCESS_KEY=value
```

When `MINIO_ENDPOINT` is set, MinIO will be used instead of S3.
