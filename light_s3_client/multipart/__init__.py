"""
Multipart upload operations for the light-s3-client.
This module contains functions for handling large file uploads using multipart upload.
"""

from ..exceptions import UnknownBucketError, BucketNotFound, AccessDeniedToBucket
from ..version import __version__
import logging
import io
import xmltodict
import requests

log = logging.getLogger("light-s3-client")


def upload_file_multipart(
    self,
    Fileobj,
    Bucket: str,
    Key: str,
    part_size: int = 5 * 1024 * 1024,  # 5MB default
    max_parts: int = 10000
) -> requests.Response:
    """
    Upload a file to S3 using multipart upload for large files. Falls back to regular upload 
    if the file is smaller than part_size.
    
    Args:
        Fileobj: A file-like object or bytes to upload
        Bucket (str): The name of the bucket to upload to
        Key (str): The name of the key to upload to
        part_size (int, optional): Size of each part in bytes. Default is 5MB (5242880)
        max_parts (int, optional): Maximum number of parts allowed. Default is 10000
        
    Returns:
        requests.Response: Response object from the upload request
    """
    # Check if file size is small enough to use regular upload
    if hasattr(Fileobj, 'seek') and hasattr(Fileobj, 'tell'):
        Fileobj.seek(0, 2)  # Seek to end
        file_size = Fileobj.tell()
        Fileobj.seek(0)  # Reset to beginning
    else:
        # For bytes or bytearray, we need to calculate size differently
        if isinstance(Fileobj, (bytes, bytearray)):
            file_size = len(Fileobj)
        else:
            # If we can't determine size, fall back to regular upload
            return self.upload_fileobj(Fileobj, Bucket, Key)
    
    # If file is smaller than part_size, use regular upload
    if file_size <= part_size:
        return self.upload_fileobj(Fileobj, Bucket, Key)
    
    # For multipart upload
    s3_url, s3_key = self.build_vars(Key, Bucket)
    
    # Step 1: Initiate multipart upload
    init_url = f"{s3_url}?uploads"
    init_data = "<InitiateMultipartUploadResult></InitiateMultipartUploadResult>"
    headers = {
        "User-Agent": f"light-s3-client/{__version__}",
        "Content-Type": "application/xml"
    }
    auth_headers = self.create_aws_signature("POST", init_url, headers, init_data)
    headers.update(auth_headers)
    
    # Create initiate multipart upload request
    init_response = self.do_request(
        url=init_url, 
        headers=headers, 
        method="POST",
        data=init_data
    )
    
    if init_response.status_code != 200:
        log.error(f"Failed to initiate multipart upload: {init_response.text}")
        return None
        
    # Parse upload ID from response
    try:
        upload_data = xmltodict.parse(init_response.text)
        upload_id = upload_data.get("InitiateMultipartUploadResult", {}).get("UploadId")
    except Exception as e:
        log.error(f"Failed to parse upload ID: {e}")
        return None
        
    if not upload_id:
        log.error("Failed to get upload ID from response")
        return None
        
    # Step 2: Upload parts
    part_number = 1
    parts = []
    uploaded_parts = 0
    
    # Create a copy of the file object for reading
    if isinstance(Fileobj, (bytes, bytearray)):
        file_obj_copy = io.BytesIO(Fileobj)
    else:
        file_obj_copy = Fileobj
        file_obj_copy.seek(0)
        
    while True:
        # Read part data
        part_data = file_obj_copy.read(part_size)
        if not part_data:
            break
            
        # Upload part
        part_url = f"{s3_url}?partNumber={part_number}&uploadId={upload_id}"
        part_headers = {
            "User-Agent": f"light-s3-client/{__version__}",
            "Content-Type": "application/octet-stream"
        }
        auth_headers = self.create_aws_signature("PUT", part_url, part_headers, part_data)
        part_headers.update(auth_headers)
        
        part_response = self.do_request(
            url=part_url,
            headers=part_headers,
            method="PUT",
            data=part_data
        )
        
        if part_response.status_code != 200:
            log.error(f"Failed to upload part {part_number}: {part_response.text}")
            # Abort multipart upload
            self._abort_multipart_upload(Bucket, Key, upload_id)
            return None
            
        # Store part information
        etag = part_response.headers.get("ETag")
        if etag:
            parts.append({"ETag": etag, "PartNumber": part_number})
            uploaded_parts += 1
            
        part_number += 1
        
        # Check for maximum parts limit
        if part_number > max_parts:
            log.error(f"Maximum parts limit ({max_parts}) exceeded")
            # Abort multipart upload
            self._abort_multipart_upload(Bucket, Key, upload_id)
            return None
    
    # Step 3: Complete multipart upload
    complete_xml = "<CompleteMultipartUpload>"
    for part in parts:
        complete_xml += f'<Part><ETag>{part["ETag"]}</ETag><PartNumber>{part["PartNumber"]}</PartNumber></Part>'
    complete_xml += "</CompleteMultipartUpload>"
    
    complete_url = f"{s3_url}?uploadId={upload_id}"
    complete_headers = {
        "User-Agent": f"light-s3-client/{__version__}",
        "Content-Type": "application/xml"
    }
    auth_headers = self.create_aws_signature("POST", complete_url, complete_headers, complete_xml)
    complete_headers.update(auth_headers)
    
    complete_response = self.do_request(
        url=complete_url,
        headers=complete_headers,
        method="POST",
        data=complete_xml
    )
    
    if complete_response.status_code == 200:
        log.info(f"Successfully completed multipart upload for {Key} in bucket {Bucket}")
        return complete_response
    else:
        log.error(f"Failed to complete multipart upload: {complete_response.text}")
        # Abort multipart upload
        self._abort_multipart_upload(Bucket, Key, upload_id)
        return None


def _abort_multipart_upload(self, Bucket: str, Key: str, upload_id: str) -> None:
    """
    _abort_multipart_upload aborts a multipart upload.
    :param Bucket: The S3 Bucket name
    :param Key: The S3 key
    :param upload_id: The upload ID to abort
    """
    s3_url, s3_key = self.build_vars(Key, Bucket)
    abort_url = f"{s3_url}?uploadId={upload_id}"
    headers = {
        "User-Agent": f"light-s3-client/{__version__}"
    }
    auth_headers = self.create_aws_signature("DELETE", abort_url, headers)
    headers.update(auth_headers)
    
    self.do_request(url=abort_url, headers=headers, method="DELETE")
    
    log.info(f"Aborted multipart upload for {Key} in bucket {Bucket}")