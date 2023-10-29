import requests
import base64
import hmac
from hashlib import sha1
from datetime import datetime
import io


class Client:
    server: str
    bucket_name: str
    access_key: str
    secret_key: str
    date_format: str
    region: str

    def __init__(self,
                 access_key: str,
                 secret_key: str,
                 region: str,
                 server: str = None,
                 encryption="AES256") -> None:
        self.region = region
        self.server = server
        if self.server is None:
            self.server = f"https://s3-{self.region}.amazonaws.com"

        self.access_key = access_key
        self.secret_key = secret_key
        self.date_format = "%a, %d %b %Y %H:%M:%S +0000"
        self.encryption = encryption

    def download_file(self, Bucket: str, Key: str, Filename: str) -> [str, None]:
        """
        get_s3_file will download a file from a specified key in a S3 bucket
        :param Bucket: String method of the request type
        :param Key: The S3 path of the file to download
        :param Filename: String of the path where to save the file locally
        :return:
        """
        s3_url, s3_key = self.build_vars(Key, Bucket)
        _, file_name = Key.rsplit("/", 1)
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
                with open(Filename, "wb") as file_handle:
                    for chunk in response.iter_content(chunk_size=128):
                        file_handle.write(chunk)
            else:
                Filename = None
                print(f"Something went wrong downloading {s3_key}")
                print(response.text)
        except Exception as error:
            Filename = None
            print(f"Something went wrong downloading {s3_key}")
            print(error)
        return Filename

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
