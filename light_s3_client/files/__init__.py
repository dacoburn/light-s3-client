"""
File-related operations for the light-s3-client.
This module contains functions for uploading, downloading, and deleting files.
"""

from .. import Client
from ..exceptions import UnknownBucketError, BucketNotFound, AccessDeniedToBucket
from ..version import __version__
import logging
import os
import io
import requests

log = logging.getLogger("light-s3-client")


def download_file(self, Bucket: str, Key: str, Filename: str) -> str:
    """
    Download an S3 object to a local file.
    
    Args:
        Bucket (str): The name of the bucket to download from
        Key (str): The name of the key to download from
        Filename (str): The path to the file to download to
        
    Returns:
        str: The path to the downloaded file
    """
    s3_url, s3_key = self.build_vars(Key, Bucket)
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
    response = self.do_request(url=s3_url, headers=headers, stream=True)
    Client.create_download_folders(Filename)
    with open(Filename, "wb") as file_handle:
        for chunk in response.iter_content(chunk_size=128):
            file_handle.write(chunk)
    log.info(f"Downloaded key {Key} from bucket {Bucket}")
    return Filename


def upload_fileobj(
    self,
    Fileobj: io.BytesIO,
    Bucket: str,
    Key: str
) -> requests.Response:
    """
    Upload a file object to S3.
    
    Args:
        Fileobj (io.BytesIO, bytes, bytearray, io.BufferedReader, or io.TextIOWrapper): 
            A file-like object or bytes to upload
        Bucket (str): The name of the bucket to upload to
        Key (str): The name of the key to upload to
        
    Returns:
        requests.Response: Response object from the upload request
    """
    s3_url, s3_key = self.build_vars(Key, Bucket)
    # Accept bytes, io.BytesIO, io.BufferedReader, io.TextIOWrapper
    if isinstance(Fileobj, (io.BytesIO, io.BufferedReader, io.TextIOWrapper)):
        data = Fileobj
    elif isinstance(Fileobj, (bytes, bytearray)):
        data = io.BytesIO(Fileobj)
    else:
        log.error("Fileobj must be bytes, bytearray, io.BytesIO, io.BufferedReader, or io.TextIOWrapper")
        return None
    # Current time needs to be within 10 minutes of the S3 Server
    date = self._get_current_date()
    # Create the authorization Signature
    signature = self.create_aws_signature(date, s3_key, "PUT")
    # Date is needed as part of the authorization
    headers = {
        "Authorization": signature,
        "Date": date,
        "User-Agent": f"light-s3-client/{__version__}"
    }
    
    # Set Content-Type based on file extension or default to application/octet-stream
    import mimetypes
    content_type, _ = mimetypes.guess_type(Key)
    if content_type:
        headers["Content-Type"] = content_type
    else:
        headers["Content-Type"] = "application/octet-stream"
        
    # Make the request
    response = self.do_request(url=s3_url, headers=headers, data=data, method="PUT")
    if response is not None:
        log.info(f"Uploaded key {Key} to bucket {Bucket}")
    return response


def delete_file(self, Bucket: str, Key: str) -> bool:
    """
    Delete an S3 object.
    
    Args:
        Bucket (str): The name of the bucket to delete from
        Key (str): The name of the key to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    s3_url, s3_key = self.build_vars(Key, Bucket)
    # Current time needs to be within 10 minutes of the S3 Server
    date = self._get_current_date()
    # Create the authorization Signature
    signature = self.create_aws_signature(date, s3_key, "DELETE")
    # Date is needed as part of the authorization
    headers = {
        "Authorization": signature,
        "Date": date,
        "User-Agent": f"light-s3-client/{__version__}"
    }
    # Make the request
    response = self.do_request(url=s3_url, headers=headers, method="DELETE")
    if response.status_code == 204:
        log.info(f"Deleted {Key} from {Bucket}")
        return True
    else:
        log.info(f"Failed to delete {Key} from {Bucket}")
        return False


def create_download_folders(key):
    """
    create_download_folders creates the necessary folder structure for downloading files.
    :param key: The key (path) of the file to download
    """
    if "/" in key:
        folder, _ = key.rsplit("/", 1)
        if not os.path.exists(folder):
            os.makedirs(folder)