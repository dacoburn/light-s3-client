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
    create_aws_signature using the logic documented at
    https://docs.aws.amazon.com/AmazonS3/latest/API/sig-v4-authenticating-requests.html#signing-request-intro
    to generate the signature for authorization of the REST API.
    :param date: Current date string needed as part of the signing method
    :param key: String path of where the file will be accessed
    :param method: String method of the type of request
    :return: The AWS signature string
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
    _get_current_date gets the current date in the required format.
    :return: Formatted date string
    """
    date = datetime.now(timezone.utc)
    return date.strftime("%a, %d %b %Y %H:%M:%S +0000")


def _get_server_url(self):
    """
    _get_server_url returns the server URL, ensuring it has a scheme.
    :return: Formatted server URL
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
    build_vars constructs the S3 URL and key for a given file and bucket.
    :param file_name: The name of the file
    :param bucket_name: The name of the bucket
    :return: Tuple of (s3_url, s3_key)
    """
    s3_url = f"{self._get_server_url()}/{bucket_name}/{file_name}"
    s3_key = f"{bucket_name}/{file_name}"
    return s3_url, s3_key