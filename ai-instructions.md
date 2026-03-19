# light-s3-client Documentation

## Overview

The `light-s3-client` is a lightweight Python library for interacting with Amazon S3 using the REST API directly, rather than relying on the full Boto3 SDK. This approach reduces dependencies and provides a more focused implementation for specific S3 operations.

## Key Features

- **Lightweight**: Uses only `requests` and `xmltodict` dependencies
- **Direct S3 API**: Implements AWS Signature Version 4 authentication directly
- **Core S3 Operations**: Supports download, upload, delete, and list operations
- **Error Handling**: Provides specific exception types for different error conditions
- **Cross-platform**: Compatible with Python 3.8+

## Important Notes

- **Always keep `ai-instructions.md` up to date with new functionality**. New updates should go into `ai-updates.md`.
- **Completed tasks should be removed from `ai-tasks.md`** and a short summary update should be added to `ai-updates.md`.

## Supported Functions

### 1. `download_file(Bucket, Key, Filename)`
Downloads an S3 object to a local file.

**Parameters:**
- `Bucket` (str): The name of the bucket to download from
- `Key` (str): The name of the key to download from
- `Filename` (str): The path to the file to download to

### 2. `upload_fileobj(Fileobj, Bucket, Key)`
Uploads a file object to S3.

**Parameters:**
- `Fileobj` (file-like object): A file-like object to upload (must implement read method and return bytes)
- `Bucket` (str): The name of the bucket to upload to
- `Key` (str): The name of the key to upload to

### 3. `delete_file(Bucket, Key)`
Deletes an S3 object.

**Parameters:**
- `Bucket` (str): The name of the bucket to delete from
- `Key` (str): The name of the key to delete

### 4. `list_objects(Bucket, Prefix)`
Lists all keys in an S3 bucket with a given prefix.

**Parameters:**
- `Bucket` (str): The name of the bucket to list objects from
- `Prefix` (str): The prefix to use for filtering keys

### 5. `get_object(Bucket, Key)`
Checks if an S3 object exists.

**Parameters:**
- `Bucket` (str): The name of the bucket to check
- `Key` (str): The key to check for existence

### 6. `upload_file_multipart(Fileobj, Bucket, Key, part_size, max_parts)`
Upload a file to S3 using multipart upload for large files. Falls back to regular upload if the file is smaller than `part_size`.

**Parameters:**
- `Fileobj` (file-like object): A file-like object or bytes to upload
- `Bucket` (str): The name of the bucket to upload to
- `Key` (str): The name of the key to upload to
- `part_size` (int, optional): Size of each part in bytes. Default is 5MB (5242880)
- `max_parts` (int, optional): Maximum number of parts allowed. Default is 10000

### 7. `head_object(Bucket, Key)`
Checks if an S3 object exists and returns its metadata.

**Parameters:**
- `Bucket` (str): The name of the bucket to check
- `Key` (str): The key to check for existence and retrieve metadata

### 8. `put_object_tagging(Bucket, Key, Tags)`
Sets tags for an S3 object.

**Parameters:**
- `Bucket` (str): The name of the bucket
- `Key` (str): The key of the object to tag
- `Tags` (dict): Dictionary of tag key-value pairs

### 9. `get_object_tagging(Bucket, Key)`
Retrieves tags for an S3 object.

**Parameters:**
- `Bucket` (str): The name of the bucket
- `Key` (str): The key of the object to retrieve tags for

## Client Initialization Parameters

| Property | Required | Type   | Description |
|----------|----------|--------|-------------|
| region   | True     | string | The S3 region being used |
| access_key | True   | string | The AWS Access Key for API Access |
| secret_key | True   | string | The AWS Secret Key for API Access |
| server   | False    | string | An override of the HTTPS URL to use |

## Authentication

The client implements AWS Signature Version 4 authentication as documented in the AWS S3 API documentation. It handles the creation of authorization signatures required for S3 REST API requests.

## Error Handling

The client raises specific exceptions:
- `BucketNotFound`: When a bucket cannot be found
- `AccessDeniedToBucket`: When access to a bucket is denied
- `UnknownBucketError`: For other bucket-related errors

## Usage Examples

### Basic Usage
```python
from light_s3_client import Client

s3 = Client(
    region="us-west-1",
    access_key="REPLACE_ME",
    secret_key="REPLACE_ME"
)

# Download a file
s3.download_file("mybucket", "hello.txt", "/tmp/hello.txt")

# Upload a file
with open("local_file.txt", "rb") as f:
    s3.upload_fileobj(f, "mybucket", "uploaded_file.txt")

# List objects
keys = s3.list_objects("mybucket", "prefix/")

# Check if object exists
exists = s3.get_object("mybucket", "path/file.txt")
```

## Build Workflow

### Development Setup
1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Testing
Run tests using pytest:
```bash
pytest
```

### Code Quality
- Linting: `flake8`
- Formatting: `black`

### Publishing
The project uses Hatch for building and publishing:
```bash
# Build the package
hatch build

# Publish to PyPI (requires proper credentials)
hatch publish
```

## Dependencies

### Required Dependencies
- `requests~=2.31.0`
- `xmltodict~=0.13.0`

### Development Dependencies
- `pytest`
- `pytest-cov`
- `black`
- `flake8`
- `python-dotenv`

## Project Structure

```
light-s3-client/
├── light_s3_client/
│   ├── __init__.py     # Main client implementation
│   ├── exceptions.py   # Custom exception classes
│   └── version.py      # Version information
├── tests/
│   └── test_integration.py  # Integration tests
├── pyproject.toml      # Project configuration
├── README.rst          # Documentation
└── LICENSE             # License information
```

## Implementation Details

The client implements direct S3 REST API calls using:
1. **AWS Signature Version 4**: For authenticating requests
2. **Requests library**: For making HTTP requests
3. **xmltodict**: For parsing XML responses from S3
4. **Custom error handling**: For specific S3 error conditions

The implementation follows AWS documentation for signature creation and handles the necessary headers and authentication for S3 API calls.

## Development Workflow

For development tasks and tracking, please refer to:
- `ai-tasks.md` - Current tasks and improvements needed
- `ai-updates.md` - Summary of completed updates and changes