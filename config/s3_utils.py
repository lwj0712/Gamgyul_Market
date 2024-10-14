import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings

# S3 클라이언트 설정
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


def upload_to_s3(file, object_name):
    try:
        s3_client.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, object_name)
        return f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{object_name}"
    except NoCredentialsError:
        return None
