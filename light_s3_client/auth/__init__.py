"""
Authentication-related operations for the light-s3-client.
This module contains functions for AWS signature creation and authentication.
"""

import base64
import hmac
from hashlib import sha256
from datetime import datetime, timezone
from ..version import __version__


def create_aws_signature(self, date, key, method) -> str:
    """
    Create AWS Signature Version 4 for S3 authentication.
    
    Implements the AWS Signature Version 4 signing process as documented in the AWS S3 API.
    
    Args:
        date (str): Current date string needed as part of the signing method
        key (str): String path of where the file will be accessed
        method (str): String method of the type of request (GET, PUT, DELETE, etc.)
        
    Returns:
        str: The AWS signature string
    """
    string_to_sign = f"{method}\n\n\n{date}\n/{key}".encode(
        "UTF-8")
    # log.error(string_to_sign)
    signature = base64.encodebytes(
        hmac.new(
            self.secret_key.encode("UTF-8"), string_to_sign, sha256
        ).digest()
    ).strip()
    signature = f"AWS {self.access_key}:{signature.decode()}"
    # log.error(signature)
    return signature


def _get_current_date(self):
    """
    Get the current date in the required format for AWS signature.
    
    Returns:
        str: Formatted date string in UTC
    """
    date = datetime.now(timezone.utc)
    return date.strftime("%a, %d %b %Y %H:%M:%S +0000")


def _get_server_url(self):
    """
    Get the server URL, ensuring it has a scheme.
    
    Returns:
        str: Formatted server URL
    """
    # Returns the server URL, ensuring it has a scheme
    if self.server:
        if self.server.startswith("http://") or self.server.startswith("https://"):
            return self.server.rstrip('/')
        else:
            return f"https://{self.server.strip('/')}"
    else:
        return f"https://s3-{self.region}.{self.base_url}"


def build_vars(self, file_name: str, bucket_name) -> tuple[str, str]:
    """
    Construct the S3 URL and key for a given file and bucket.
    
    Args:
        file_name (str): The name of the file
        bucket_name (str): The name of the bucket
        
    Returns:
        tuple[str, str]: Tuple of (s3_url, s3_key)
    """
    s3_url = f"{self._get_server_url()}/{bucket_name}/{file_name}"
    s3_key = f"{bucket_name}/{file_name}"
    return s3_url, s3_key