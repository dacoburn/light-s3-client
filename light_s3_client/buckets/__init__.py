"""
Bucket-related operations for the light-s3-client.
This module contains functions for managing S3 buckets.
"""

from .. import Client
from ..exceptions import UnknownBucketError, BucketNotFound, AccessDeniedToBucket
from ..version import __version__
import logging

log = logging.getLogger("light-s3-client")


def list_objects(self, Bucket: str, Prefix: str) -> list:
    """
    list_objects lists all keys in an S3 bucket with a given prefix.
    :param Bucket: The name of the bucket to list objects from
    :param Prefix: The prefix to use for filtering keys
    :return: List of object keys
    """
    s3_url = f"{self._get_server_url()}/{Bucket}/?list-type=2&prefix={Prefix}"
    s3_key = f"{Bucket}/"
    # Current time needs to be within 10 minutes of the S3 Server
    date = self._get_current_date()
    # Create the authorization Signature
    signature = self.create_aws_signature(date, s3_key, "GET")
    # Date is needed as part of the authorization
    headers = {
        "Authorization": signature,
        "Date": date,
        "User-Agent": f"light-s3-client/{__version__}"
    }
    # Make the request
    response = self.do_request(url=s3_url, headers=headers)
    log.info(f"Retrieved keys for bucket {Bucket} with prefix {Prefix}")
    data = Client.get_bucket_keys(response.text, Prefix)
    return data


def get_object(self, Bucket: str, Key: str) -> bool:
    """
    get_object checks if an S3 object exists.
    :param Bucket: The name of the bucket to check
    :param Key: The key to check for existence
    :return: True if object exists, False otherwise
    """
    s3_url = f"{self._get_server_url()}/{Bucket}/{Key}"
    s3_key = f"{Bucket}/{Key}"
    # Current time needs to be within 10 minutes of the S3 Server
    date = self._get_current_date()
    # Create the authorization Signature
    signature = self.create_aws_signature(date, s3_key, "GET")
    # Date is needed as part of the authorization
    headers = {
        "Authorization": signature,
        "Date": date,
        "User-Agent": f"light-s3-client/{__version__}"
    }
    # Make the request
    exists = False
    try:
        response = self.do_request(url=s3_url, headers=headers, stream=True)
        if response.status_code == 200:
            log.info(f"key {Key} from bucket {Bucket} exists")
            exists = True
    except BucketNotFound:
        log.info(f"{Key} not found in {Bucket}")
    return exists


def head_object(self, Bucket: str, Key: str) -> dict:
    """
    head_object checks if an S3 object exists and returns metadata.
    :param Bucket: The S3 Bucket name
    :param Key: The S3 key to check
    :return: Dictionary containing object metadata
    """
    s3_url = f"{self._get_server_url()}/{Bucket}/{Key}"
    s3_key = f"{Bucket}/{Key}"
    # Current time needs to be within 10 minutes of the S3 Server
    date = self._get_current_date()
    # Create the authorization Signature
    signature = self.create_aws_signature(date, s3_key, "HEAD")
    # Date is needed as part of the authorization
    headers = {
        "Authorization": signature,
        "Date": date,
        "User-Agent": f"light-s3-client/{__version__}"
    }
    # Make the request
    response = self.do_request(url=s3_url, headers=headers, method="HEAD")
    if response.status_code == 200:
        # Return metadata from response headers
        metadata = {
            "Content-Type": response.headers.get("Content-Type"),
            "Content-Length": response.headers.get("Content-Length"),
            "ETag": response.headers.get("ETag"),
            "Last-Modified": response.headers.get("Last-Modified"),
            "Server": response.headers.get("Server"),
            "x-amz-request-id": response.headers.get("x-amz-request-id"),
            "x-amz-id-2": response.headers.get("x-amz-id-2")
        }
        # Remove None values
        metadata = {k: v for k, v in metadata.items() if v is not None}
        log.info(f"Object {Key} from bucket {Bucket} exists with metadata")
        return metadata
    else:
        log.info(f"Object {Key} not found in {Bucket}")
        return {}


def get_bucket_keys(xml_text: str, prefix: str) -> list:
    """
    get_bucket_keys parses the XML response from S3 list objects request.
    :param xml_text: XML response text from S3
    :param prefix: The prefix used for filtering keys
    :return: List of object keys
    """
    import xmltodict
    xml_data = xmltodict.parse(xml_text)
    results = xml_data.get("ListBucketResult")
    if prefix is None:
        prefix = ""
    if results is not None:
        contents = results.get("Contents")
    else:
        contents = None
    data = []
    if contents is not None:
        # Ensure contents is always a list
        if isinstance(contents, dict):
            contents = [contents]
        for content in contents:
            key = content.get("Key")
            if key is not None and key.rstrip("/") != prefix.rstrip("/"):
                data.append(key)
    return data