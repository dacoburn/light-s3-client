# light-s3-client

## Purpose

The AWS Boto3 Client is quite heavy, and usually specific functionality is needed. This module only implements needed functionality using the requests library and the S3 REST API.

Reference doc used for this creation: https://docs.aws.amazon.com/AmazonS3/latest/API/sig-v4-authenticating-requests.html#signing-request-intro

*Note: The parameter names and function names were copied from the Boto3 S3 Client. It does not necessarily have all the options for the function*

## Supported Functions

### Client.download_file(Bucket, Key, Filename)

Download an S3 object to a file.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
s3.download_file("mybucket", "hello.txt", "/tmp/hello.txt")
```

**PARAMETERS:**

- **Bucket (str)** – The name of the bucket to download from.
- **Key (str)** – The name of the key to download from.
- **Filename (str)** – The path to the file to download to.

### Client.upload_fileobj(Fileobj, Bucket, Key)

Upload a file object to S3. The Content-Type header is automatically inferred from the file extension.

**Usage:**

```python
from light_s3_client import Client
import json


def get_file_contents(file_name) -> bytes:
    file_handle = open(file_name, "r")
    content = json.load(file_handle)
    str_content = json.dumps(content)
    file_handle.close()
    data = str_content.encode("utf-8")
    return data


s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
upload_data = get_file_contents("example.json")
s3.upload_fileobj(upload_data, "example-bucket", "path/example.json")
```

**PARAMETERS:**

- **Fileobj (bytes, io.BytesIO, io.BufferedReader, or io.TextIOWrapper)** – A file-like object or bytes to upload.
- **Bucket (str)** – The name of the bucket to upload to.
- **Key (str)** – The name of the key to upload to.

### Client.upload_file_multipart(Fileobj, Bucket, Key, part_size, max_parts)

Upload a file to S3 using multipart upload for large files. Falls back to regular upload if the file is smaller than `part_size`.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
with open("large_file.bin", "rb") as f:
    s3.upload_file_multipart(f, "example-bucket", "path/large_file.bin")
```

**PARAMETERS:**

- **Fileobj (bytes, io.BytesIO, io.BufferedReader, or io.TextIOWrapper)** – A file-like object or bytes to upload.
- **Bucket (str)** – The name of the bucket to upload to.
- **Key (str)** – The name of the key to upload to.
- **part_size (int, optional)** – Size of each part in bytes. Default is 5MB (5242880).
- **max_parts (int, optional)** – Maximum number of parts allowed. Default is 10000.

### Client.delete_file(Bucket, Key)

Delete an S3 object. Returns `True` if the deletion was successful, `False` otherwise.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
result = s3.delete_file("example-bucket", "path/example.json")
print(f"Delete result: {result}")  # True if successful, False otherwise
```

### Client.list_objects(Bucket, Prefix)

List all keys in an S3 bucket with a given prefix.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
objects = s3.list_objects("example-bucket", "path/")
print(f"Found {len(objects)} objects")
```

### Client.get_object(Bucket, Key)

Check if an S3 object exists. Returns `True` if the object exists, `False` otherwise.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
exists = s3.get_object("example-bucket", "path/example.json")
print(f"Object exists: {exists}")  # True if exists, False otherwise
```

### Client.head_object(Bucket, Key)

Check if an S3 object exists and return its metadata. Returns a dictionary with metadata if the object exists, or an empty dictionary otherwise.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
metadata = s3.head_object("example-bucket", "path/example.json")
print(f"Object metadata: {metadata}")  # Dictionary with metadata or empty dict
```

### Client.put_object_tagging(Bucket, Key, Tags)

Set tags for an S3 object. Returns `True` if successful, `False` otherwise.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
tags = {"Environment": "Production", "Owner": "John Doe"}
result = s3.put_object_tagging("example-bucket", "path/example.json", tags)
print(f"Tagging result: {result}")  # True if successful, False otherwise
```

### Client.get_object_tagging(Bucket, Key)

Retrieve tags for an S3 object. Returns a dictionary of tag key-value pairs if successful, or an empty dictionary otherwise.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
tags = s3.get_object_tagging("example-bucket", "path/example.json")
print(f"Object tags: {tags}")  # Dictionary with tags or empty dict
```

## Client Initialization Parameters

| Property | Required | Type   | Description |
|----------|----------|--------|-------------|
| region     | True     | string | The S3 region being used |
| access_key | True     | string | The AWS Access Key for API Access |
| secret_key | True     | string | The AWS Secret Key for API Access |
| server     | False    | string | An override of the HTTPS URL to use |

## Authentication

This library implements AWS Signature Version 4 authentication directly, without relying on the Boto3 SDK. It handles all the necessary cryptographic operations to authenticate requests to S3-compatible services.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
deleted = s3.delete_file("example-bucket", "path/example.json")
```

**PARAMETERS:**

- **Bucket (str)** – The name of the bucket to delete from.
- **Key (str)** – The name of the key to delete.

### Client.list_objects(Bucket, Prefix)

Lists all keys in an S3 bucket with a given prefix.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
keys = s3.list_objects("example-bucket", "prefix")
```

**PARAMETERS:**

- **Bucket (str)** – The name of the bucket to list objects from.
- **Prefix (str)** – The prefix to use as the search for getting keys from the bucket.

### Client.get_object(Bucket, Key)

Returns if an object exists or not.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
exists = s3.get_object("example-bucket", "path/file.txt")
```

**PARAMETERS:**

- **Bucket (str)** – The name of the bucket to check.
- **Key (str)** – The key to check if it exists in the bucket.

### Client.head_object(Bucket, Key)

Checks if an S3 object exists and returns its metadata (Content-Type, Content-Length, ETag, Last-Modified, etc.).

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
metadata = s3.head_object("example-bucket", "path/file.txt")
```

**PARAMETERS:**

- **Bucket (str)** – The name of the bucket to check.
- **Key (str)** – The key to check for existence and retrieve metadata.

**RETURNS:** Dictionary containing object metadata, or an empty dictionary if the object does not exist.

### Client.put_object_tagging(Bucket, Key, Tags)

Sets tags for an S3 object.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
s3.put_object_tagging("example-bucket", "path/file.txt", {"env": "prod", "team": "data"})
```

**PARAMETERS:**

- **Bucket (str)** – The name of the bucket.
- **Key (str)** – The key of the object to tag.
- **Tags (dict)** – Dictionary of tag key-value pairs.

**RETURNS:** `True` if successful, `False` otherwise.

### Client.get_object_tagging(Bucket, Key)

Retrieves tags for an S3 object.

**Usage:**

```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)
tags = s3.get_object_tagging("example-bucket", "path/file.txt")
```

**PARAMETERS:**

- **Bucket (str)** – The name of the bucket.
- **Key (str)** – The key of the object to retrieve tags for.

**RETURNS:** Dictionary of tag key-value pairs, or an empty dictionary if no tags exist.

### Client Parameters

| Property   | Required | Type   | Description                                                              |
|------------|----------|--------|--------------------------------------------------------------------------|
| region     | True     | string | The S3 region being used. This ends up as part of the Server URL         |
| access_key | True     | string | The AWS Access Key for API Access                                        |
| secret_key | True     | string | The AWS Secret Key for API Access                                        |
| server     | False    | string | An override of the HTTPS URL to use. When used then `region` is not used |
