import json
import requests
from requests import Response
import base64
import hmac
from hashlib import sha1
from datetime import datetime
import io
import xmltodict
import os
import logging
from typing import Union
from light_s3_client.exceptions import BucketNotFound, AccessDeniedToBucket, UnknownBucketError


__author__ = 'socket.dev'
__version__ = '0.0.20'
__all__ = [
    "Client",
]


log = logging.getLogger("light-s3-client")
log.addHandler(logging.NullHandler())


def do_request(
        url: str,
        headers: dict,
        data: Union[bytes, io.TextIOWrapper, io.BufferedReader, dict] = None,
        stream: bool = True,
        method: str = "GET",
        bucket: str = None,
        key: str = None,
        prefix: str = None
) -> Union[None, Response]:
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=data,
            stream=stream
        )
    except Exception as error:
        msg = {
            'error': f"Something went wrong performing {method} on {url}",
            'data': str(error)
        }
        error_msg = json.dumps(msg)
        response = Response()
        response.status_code = 500
        response._content = bytes(error_msg, 'utf-8')
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
        self.base_url = "amazonaws.com"
        if self.server is None:
            self.server = f"https://s3-{self.region}.{self.base_url}"
        self.access_key = access_key
        self.secret_key = secret_key
        self.date_format = "%a, %d %b %Y %H:%M:%S +0000"
        self.encryption = encryption

    def list_objects(self, Bucket: str, Prefix: str = None) -> list:
        """
        get_s3_file will download a file from a specified key in a S3 bucket
        :param Bucket: String method of the request type
        :param Prefix: The S3 path of the file to download
        :return:
        """
        s3_url = f"https://{Bucket}.s3.{self.base_url}/?list-type=2"
        if Prefix is not None:
            s3_url += f"&prefix={Prefix}"
        s3_key = f"{Bucket}/"
        # Current time needs to be within 10 minutes of the S3 Server
        date = datetime.utcnow()
        date = date.strftime("%a, %d %b %Y %H:%M:%S +0000")
        # Create the authorization Signature
        signature = self.create_aws_signature(date, s3_key, "GET")
        # Date is needed as part of the authorization
        headers = {
            "Authorization": signature,
            "Date": date
        }
        # Make the request
        response = do_request(url=s3_url, headers=headers)
        log.info(f"Retrieved keys for bucket {Bucket} with prefix {Prefix}")
        data = Client.get_bucket_keys(response.text, Prefix)
        return data

    @staticmethod
    def get_bucket_keys(xml_text: str, prefix: str) -> list:
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
            for content in contents:
                key = content.get("Key")
                if key is not None and key.rstrip("/") != prefix.rstrip("/"):
                    data.append(key)
        return data

    def get_object(self, Bucket: str, Key: str) -> bool:
        """
        get_s3_file will download a file from a specified key in a S3 bucket
        :param Bucket: String method of the request type
        :param Key: The S3 path of the file to download
        :return:
        """
        s3_url = f"https://{Bucket}.s3.{self.base_url}/{Key}"
        s3_key = f"{Bucket}/{Key}"
        # Current time needs to be within 10 minutes of the S3 Server
        date = datetime.utcnow()
        date = date.strftime("%a, %d %b %Y %H:%M:%S +0000")
        # Create the authorization Signature
        signature = self.create_aws_signature(date, s3_key, "GET")
        # Date is needed as part of the authorization
        headers = {
            "Authorization": signature,
            "Date": date
        }
        # Make the request
        exists = False
        try:
            response = do_request(url=s3_url, headers=headers, stream=True)
            if response.status_code == 200:
                log.info(f"key {Key} from bucket {Bucket} exists")
                exists = True
        except BucketNotFound:
            log.info(f"{Key} not found in {Bucket}")
        return exists

    def download_file(self, Bucket: str, Key: str, Filename: str) -> str:
        """
        get_s3_file will download a file from a specified key in a S3 bucket
        :param Bucket: String method of the request type
        :param Key: The S3 path of the file to download
        :param Filename: String of the path where to save the file locally
        :return:
        """
        s3_url, s3_key = self.build_vars(Key, Bucket)
        # Current time needs to be within 10 minutes of the S3 Server
        date = datetime.utcnow()
        date = date.strftime("%a, %d %b %Y %H:%M:%S +0000")
        # Create the authorization Signature
        signature = self.create_aws_signature(date, s3_key, "GET")
        # Date is needed as part of the authorization
        headers = {
            "Authorization": signature,
            "Date": date
        }
        # Make the request
        response = do_request(url=s3_url, headers=headers, stream=True)
        Client.create_download_folders(Filename)
        with open(Filename, "wb") as file_handle:
            for chunk in response.iter_content(chunk_size=128):
                file_handle.write(chunk)
        log.info(f"Downloaded key {Key} from bucket {Bucket}")
        return Filename

    @staticmethod
    def create_download_folders(key):
        if "/" in key:
            folder, _ = key.rsplit("/", 1)
            if not os.path.exists(folder):
                os.makedirs(folder)

    def upload_fileobj(
        self,
        Fileobj: Union[bytes, io.TextIOWrapper, io.BufferedReader],
        Bucket: str,
        Key: str
    ) -> [requests.Response, None]:
        """
        upload_fileobj uploaded a file to a S3 Bucket
        :param Bucket: The S3 Bucket name
        :param Key: String path of where the file is uploaded to
        :param Fileobj: takes either a bytes object or file like object to upload
        :return:
        """
        # Create a binary file object using io
        # report_file = io.BytesIO(data.encode("utf-8"))
        s3_url, s3_key = self.build_vars(Key, Bucket)
        if type(Fileobj) == io.TextIOWrapper or type(Fileobj) == io.BufferedReader:
            data = Fileobj
        else:
            data = io.BytesIO(Fileobj)
        # Current time needs to be within 10 minutes of the S3 Server
        date = datetime.utcnow()
        date = date.strftime("%a, %d %b %Y %H:%M:%S +0000")
        # Create the authorization Signature
        signature = self.create_aws_signature(date, s3_key, "PUT")
        # Date is needed as part of the authorization
        headers = {
            "Authorization": signature,
            "Date": date
        }
        # Make the request
        response = do_request(url=s3_url, headers=headers, data=data, method="PUT")
        log.info(f"Uploaded key {Key} to bucket {Bucket}")
        return response

    def delete_file(self, Bucket: str, Key: str) -> bool:
        """
        delete_file will delete the file from the bucket
        :param Bucket: The S3 Bucket name
        :param Key: Filename of the file to delete
        :return:
        """
        s3_url, s3_key = self.build_vars(Key, Bucket)
        # Current time needs to be within 10 minutes of the S3 Server
        date = datetime.utcnow()
        date = date.strftime(self.date_format)
        # Create the authorization Signature
        signature = self.create_aws_signature(date, s3_key, "DELETE")
        # Date is needed as part of the authorization
        headers = {
            "Authorization": signature,
            "Date": date
        }
        # Make the request
        is_error = False
        response = do_request(url=s3_url, headers=headers, method="DELETE")
        if response.status_code == 204:
            log.info(f"Deleted {Key} from {Bucket}")
        return is_error

    def create_aws_signature(self, date, key, method) -> (str, str):
        """
        create_aws_signature using the logic documented at
        https://docs.aws.amazon.com/AmazonS3/latest/API/sig-v4-authenticating-requests.html#signing-request-intro
        to generate the signature for authorization of the REST API.
        :param date: Current date string needed as part of the signing method
        :param key: String path of where the file will be accessed
        :param method: String method of the type of request
        :return:
        """
        string_to_sign = f"{method}\n\n\n{date}\n/{key}".encode(
            "UTF-8")
        # log.error(string_to_sign)
        signature = base64.encodebytes(
            hmac.new(
                self.secret_key.encode("UTF-8"), string_to_sign, sha1
            ).digest()
        ).strip()
        signature = f"AWS {self.access_key}:{signature.decode()}"
        # log.error(signature)
        return signature

    def build_vars(self, file_name: str, bucket_name) -> (str, str):
        s3_url = f"{self.server}/{bucket_name}/{file_name}"
        s3_key = f"{bucket_name}/{file_name}"
        return s3_url, s3_key
