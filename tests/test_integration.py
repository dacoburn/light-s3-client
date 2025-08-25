import os
import io
import tempfile
import pytest
from light_s3_client import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

S3_SERVER = os.getenv("s3_server")
S3_ACCESS_KEY = os.getenv("s3_access_key")
S3_SECRET_KEY = os.getenv("s3_secret_key")
S3_BUCKET = os.getenv("s3_bucket")
S3_REGION = os.getenv("s3_region", "us-east-1")

@pytest.fixture(scope="module")
def s3_client():
    return Client(
        access_key=S3_ACCESS_KEY,
        secret_key=S3_SECRET_KEY,
        region=S3_REGION,
        server=S3_SERVER
    )

@pytest.fixture(scope="module")
def test_key():
    return "integration_test_file.txt"

@pytest.fixture(scope="module")
def test_content():
    return b"Integration test content."


def test_upload_fileobj(s3_client, test_key, test_content):
    fileobj = io.BytesIO(test_content)
    response = s3_client.upload_fileobj(fileobj, S3_BUCKET, test_key)
    print(f"Uploaded file to bucket: {S3_BUCKET}, key: {test_key}, status: {getattr(response, 'status_code', None)}")
    assert response is not None
    assert response.status_code in (200, 201)


def test_list_objects(s3_client, test_key):
    objects = s3_client.list_objects(S3_BUCKET, Prefix="integration_test")
    print(f"Listing files in bucket: {S3_BUCKET} with prefix 'integration_test': {len(objects)} keys found")
    assert isinstance(objects, list)
    assert any(test_key in obj for obj in objects)


def test_get_object(s3_client, test_key):
    exists = s3_client.get_object(S3_BUCKET, test_key)
    print(f"Checked existence of key: {test_key} in bucket: {S3_BUCKET} - Exists: {exists}")
    assert exists is True


def test_download_file(s3_client, test_key, test_content):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        filename = tmp.name
    try:
        s3_client.download_file(S3_BUCKET, test_key, filename)
        with open(filename, "rb") as f:
            data = f.read()
        print(f"Downloaded file from bucket: {S3_BUCKET}, key: {test_key}, bytes: {len(data)}")
        assert data == test_content
    finally:
        os.remove(filename)


def test_delete_file(s3_client, test_key):
    s3_client.delete_file(S3_BUCKET, test_key)
    print(f"Deleted key: {test_key} from bucket: {S3_BUCKET}")
    exists = s3_client.get_object(S3_BUCKET, test_key)
    print(f"Checked existence after delete for key: {test_key} in bucket: {S3_BUCKET} - Exists: {exists}")
    assert exists is False