"""
light-s3-client - A lightweight Python library for interacting with Amazon S3.

This module provides a simplified interface to S3 operations without requiring the full Boto3 SDK.
"""

import json
import requests
from requests import Response
import base64
import hmac
from hashlib import sha256
from datetime import datetime, timezone
import io
import xmltodict
import os
import logging
from typing import Union
from .version import __version__
from .exceptions import UnknownBucketError, BucketNotFound, AccessDeniedToBucket
from . import buckets, files, objects, auth, multipart

__author__ = 'socket.dev'
__all__ = [
    "Client",
]


log = logging.getLogger("light-s3-client")
log.addHandler(logging.NullHandler())


def do_request(
        url: str,
        headers: dict,
        data: Union[bytes, io.TextIOWrapper, io.BufferedReader, dict, None] = None,
        stream: bool = True,
        method: str = "GET",
        bucket: str = None,
        key: str = None,
        prefix: str = None
) -> Union[Response, None]:
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            stream=stream
        )
    except requests.exceptions.ConnectionError as error:
        msg = {
            'error': f"Connection error performing {method} on {url}",
            'data': str(error)
        }
        error_msg = json.dumps(msg)
        response = Response()
        response.status_code = 500
        response._content = bytes(error_msg, 'utf-8')
        log.error(f"Connection error: {error}")
        return response
    except requests.exceptions.Timeout as error:
        msg = {
            'error': f"Timeout error performing {method} on {url}",
            'data': str(error)
        }
        error_msg = json.dumps(msg)
        response = Response()
        response.status_code = 500
        response._content = bytes(error_msg, 'utf-8')
        log.error(f"Timeout error: {error}")
        return response
    except requests.exceptions.RequestException as error:
        msg = {
            'error': f"Request error performing {method} on {url}",
            'data': str(error)
        }
        error_msg = json.dumps(msg)
        response = Response()
        response.status_code = 500
        response._content = bytes(error_msg, 'utf-8')
        log.error(f"Request error: {error}")
        return response
    except Exception as error:
        msg = {
            'error': f"Unexpected error performing {method} on {url}",
            'data': str(error)
        }
        error_msg = json.dumps(msg)
        response = Response()
        response.status_code = 500
        response._content = bytes(error_msg, 'utf-8')
        log.error(f"Unexpected error: {error}")
        return response
    msg_items = [f"url: {url}", f"method: {method}"]
    if bucket is not None:
        msg_items.append(f"bucket: {bucket}")
    if prefix is not None:
        msg_items.append(f"prefix: {prefix}")
    if key is not None:
        msg_items.append(f"key: {key}")
    msg = ", ".join(msg_items)
    if response.status_code == 200 or response.status_code == 204:
        return response
    elif response.status_code == 403:
        raise AccessDeniedToBucket(msg)
    elif response.status_code == 404:
        raise BucketNotFound(msg)
    else:
        # Parse the S3 error response for more detailed error information
        try:
            error_data = xmltodict.parse(response.text)
            error_code = error_data.get("Error", {}).get("Code", "Unknown")
            error_message = error_data.get("Error", {}).get("Message", response.text)
            detailed_msg = f"{error_code}: {error_message}"
            raise UnknownBucketError(detailed_msg)
        except Exception:
            raise UnknownBucketError(response.text)


class Client:
    server: str
    bucket_name: str
    access_key: str
    secret_key: str
    date_format: str
    region: str
    base_url: str

    def __init__(self,
                 access_key: str,
                 secret_key: str,
                 region: str,
                 server: str = None,
                 encryption="AES256") -> None:
        self.region = region
        self.server = server
        self.base_url = "s3.amazonaws.com"
        if self.server is None:
            self.server = f"https://s3-{self.region}.{self.base_url}"
        self.access_key = access_key
        self.secret_key = secret_key
        self.date_format = "%a, %d %b %Y %H:%M:%S +0000"
        self.encryption = encryption

    # Import methods from submodules
    # These will be set dynamically after the class definition
    pass


# Set up method bindings after class definition
import light_s3_client.buckets as buckets_module
import light_s3_client.files as files_module
import light_s3_client.objects as objects_module
import light_s3_client.auth as auth_module
import light_s3_client.multipart as multipart_module

# Bind methods to the Client class
Client.list_objects = buckets_module.list_objects
Client.get_object = buckets_module.get_object
Client.head_object = buckets_module.head_object
Client.get_bucket_keys = buckets_module.get_bucket_keys

Client.download_file = files_module.download_file
Client.upload_fileobj = files_module.upload_fileobj
Client.delete_file = files_module.delete_file
Client.create_download_folders = files_module.create_download_folders

Client.put_object_tagging = objects_module.put_object_tagging
Client.get_object_tagging = objects_module.get_object_tagging

Client.upload_file_multipart = multipart_module.upload_file_multipart
Client._abort_multipart_upload = multipart_module._abort_multipart_upload

Client.create_aws_signature = auth_module.create_aws_signature
Client._get_current_date = auth_module._get_current_date
Client._get_server_url = auth_module._get_server_url
Client.build_vars = auth_module.build_vars
