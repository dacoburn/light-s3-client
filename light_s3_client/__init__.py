import requests
import base64
import hmac
from hashlib import sha1
from datetime import datetime
import io
import xmltodict
import os


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

    def list_objects(self, Bucket: str, Prefix: str) -> list:
        """
        get_s3_file will download a file from a specified key in a S3 bucket
        :param Bucket: String method of the request type
        :param Prefix: The S3 path of the file to download
        :return:
        """
        s3_url = f"https://{Bucket}.s3.{self.base_url}/?list-type=2&prefix={Prefix}"
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
        try:
            response = requests.get(url=s3_url, headers=headers, stream=True)
            if response.status_code == 200:
                data = Client.get_bucket_keys(response.text, Prefix)
            else:
                data = []
                print(f"Something went wrong getting {Prefix}")
                print(response.text)
        except Exception as error:
            data = []
            print(f"Something went wrong getting {Prefix}")
            print(error)
        return data

    @staticmethod
    def get_bucket_keys(xml_text: str, prefix: str) -> list:
        xml_data = xmltodict.parse(xml_text)
        results = xml_data.get("ListBucketResult")
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
        try:
            response = requests.get(url=s3_url, headers=headers, stream=True)
            if response.status_code == 200:
                exists = True
            else:
                exists = False
                print(f"Something went wrong getting {Key}")
                print(response.text)
        except Exception as error:
            exists = False
            print(f"Something went wrong getting {Key}")
            print(error)
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
        try:
            response = requests.get(url=s3_url, headers=headers, stream=True)
            if response.status_code == 200:
                Client.create_download_folders(Filename)
                with open(Filename, "wb") as file_handle:
                    for chunk in response.iter_content(chunk_size=128):
                        file_handle.write(chunk)
            else:
                Filename = ""
                print(f"Something went wrong downloading {s3_key}")
                print(response.text)
        except Exception as error:
            Filename = ""
            print(f"Something went wrong downloading {s3_key}")
            print(error)
        return Filename

    @staticmethod
    def create_download_folders(key):
        if "/" in key:
            folder, _ = key.rsplit("/", 1)
            if not os.path.exists(folder):
                os.makedirs(folder)

    def upload_fileobj(
            self,
            Fileobj: bytes,
            Bucket: str,
            Key: str
    ) -> [requests.Response, None]:
        """
        upload_fileobj takes a path for a file and binary data file to put in a S3
        bucket
        :param Bucket: The S3 Bucket name
        :param Key: String path of where the file is uploaded to
        :param Fileobj: Bytes object of the data being uploaded
        :return:
        """
        # Create a binary file object using io
        # report_file = io.BytesIO(data.encode("utf-8"))
        s3_url, s3_key = self.build_vars(Key, Bucket)
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
        try:
            response = requests.put(
                url=s3_url,
                headers=headers,
                data=data
            )
            if response.status_code != 200:
                print(f"Something went wrong uploading {Key}")
                print(response.text)
                response = None
        except Exception as error:
            print(f"Unable to upload {s3_key}")
            print(error)
            response = None
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
        try:
            response = requests.delete(url=s3_url, headers=headers)
            if response.status_code != 204:
                print(
                    f"Failed to perform request to delete {s3_key}")
                print(response.text)
                is_error = True
        except Exception as error:
            print(f"Failed to perform request to delete {s3_key}")
            print(error)
            is_error = True
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
        # print(string_to_sign)
        signature = base64.encodebytes(
            hmac.new(
                self.secret_key.encode("UTF-8"), string_to_sign, sha1
            ).digest()
        ).strip()
        signature = f"AWS {self.access_key}:{signature.decode()}"
        # print(signature)
        return signature

    def build_vars(self, file_name: str, bucket_name) -> (str, str):
        s3_url = f"{self.server}/{bucket_name}/{file_name}"
        s3_key = f"{bucket_name}/{file_name}"
        return s3_url, s3_key
