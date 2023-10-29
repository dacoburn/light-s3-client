
light-s3-client
###############

Purpose
-------
The AWS Boto3 Client is quite heavy, and usually specific functionality is needed. This module only implements needed functionality uses the requests library and the S3 Resp API.

Reference doc used for this creation: https://docs.aws.amazon.com/AmazonS3/latest/API/sig-v4-authenticating-requests.html#signing-request-intro

*Note: The parameter names and function names were copied from the Boto3 S3 Client. It does necessarily have all the options for the function*

Supported Functions
-------------------

Client.download_file(Bucket, Key, Filename)
""""""""""""""""""""""""""""""""""""""""""""""

Download an S3 object to a file

**Usage:**

.. code-block:: python

    import light_s3_client

    s3 = light_s3_client.Client(
        region="us-west-1",
        access_key="REPLACE_ME",
        secret_key="REPLACE_ME"
    )
    s3.download_file("mybucket", "hello.txt", "/tmp/hello.txt")



**PARAMETERS:**

- **Bucket (str)** – The name of the bucket to download from.
- **Key (str)** – The name of the key to download from. 
- **Filename (str)** – The path to the file to download to.

Client.upload_fileobj(Fileobj, Bucket, Key)
"""""""""""""""""""""""""""""""""""""""""""

Upload a File Object to S3

**Usage:**

.. code-block:: python

    import light_s3_client
    import json


    def get_file_contents(file_name) -> bytes:
        file_handle = open(file_name, "r")
        content = json.load(file_handle)
        str_content = json.dumps(content)
        file_handle.close()
        data = str_content.encode("utf-8")
        return data


    s3 = light_s3_client.Client(
        region="us-west-1",
        access_key="REPLACE_ME",
        secret_key="REPLACE_ME"
    )
    upload_data = get_file_contents("example.json")
    s3.upload_fileobj(upload_data, "example-bucket", "/path/example.json")

**PARAMETERS:**

- **Fileobj (a file-like object)** – A file-like object to upload. At a minimum, it must implement the read method, and must return bytes.
- **Bucket (str)** – The name of the bucket to upload to. 
- **Key (str)** – The name of the key to upload to.

Client.delete_object(Bucket, Key)
"""""""""""""""""""""""""""""""""

Delete a S3 object

**Usage:**

.. code-block:: python

    from src import s3

    s3 = s3.Client(
        region="us-west-1",
        access_key="REPLACE_ME",
        secret_key="REPLACE_ME"
    )
    s3.delete_file("example-bucket", "/path/example.json")

**PARAMETERS:**

- **Bucket (str)** – The name of the bucket to upload to. 
- **Key (str)** – The name of the key to upload to.(Fileobj, Bucket, Key)


Client Parameters
"""""""""""""""""

========== ======== ====== =========================================================================
property   Required type   description
========== ======== ====== =========================================================================
region     True     string The S3 region being used. This ends up as part of the Server URL
access_key True     string The AWS Access Key for API Access
secret_key True     string The AWS Secret Key for API Access
server     False    string An override of the HTTPS URL to use. When used then `region` is not used
========== ======== ====== =========================================================================


