"""
Object-related operations for the light-s3-client.
This module contains functions for managing S3 object tags.
"""

from .. import Client
from ..exceptions import UnknownBucketError, BucketNotFound, AccessDeniedToBucket
from ..version import __version__
import logging
import xmltodict

log = logging.getLogger("light-s3-client")


def put_object_tagging(self, Bucket: str, Key: str, Tags: dict) -> bool:
    """
    put_object_tagging sets tags for an S3 object.
    :param Bucket: The S3 Bucket name
    :param Key: The S3 key to tag
    :param Tags: Dictionary of tag key-value pairs
    :return: True if successful, False otherwise
    """
    s3_url, s3_key = self.build_vars(Key, Bucket)
    date = self._get_current_date()
    signature = self.create_aws_signature(date, s3_key, "PUT")
    
    headers = {
        "Authorization": signature,
        "Date": date,
        "User-Agent": f"light-s3-client/{__version__}",
        "Content-Type": "application/xml"
    }
    
    # Create XML for tags
    tag_xml = "<Tagging><TagSet>"
    for key, value in Tags.items():
        tag_xml += f"<Tag><Key>{key}</Key><Value>{value}</Value></Tag>"
    tag_xml += "</TagSet></Tagging>"
    
    tag_url = f"{s3_url}?tagging"
    response = self.do_request(
        url=tag_url,
        headers=headers,
        method="PUT",
        data=tag_xml
    )
    
    if response.status_code == 200:
        log.info(f"Successfully tagged object {Key} in bucket {Bucket}")
        return True
    else:
        log.error(f"Failed to tag object {Key}: {response.text}")
        return False


def get_object_tagging(self, Bucket: str, Key: str) -> dict:
    """
    get_object_tagging retrieves tags for an S3 object.
    :param Bucket: The S3 Bucket name
    :param Key: The S3 key to get tags for
    :return: Dictionary of tag key-value pairs
    """
    s3_url, s3_key = self.build_vars(Key, Bucket)
    date = self._get_current_date()
    signature = self.create_aws_signature(date, s3_key, "GET")
    
    headers = {
        "Authorization": signature,
        "Date": date,
        "User-Agent": f"light-s3-client/{__version__}"
    }
    
    tag_url = f"{s3_url}?tagging"
    response = self.do_request(
        url=tag_url,
        headers=headers,
        method="GET"
    )
    
    if response.status_code == 200:
        try:
            tag_data = xmltodict.parse(response.text)
            tag_set = tag_data.get("Tagging", {}).get("TagSet", {}).get("Tag", [])
            
            tags = {}
            if isinstance(tag_set, list):
                for tag in tag_set:
                    tags[tag.get("Key")] = tag.get("Value")
            elif isinstance(tag_set, dict):
                tags[tag_set.get("Key")] = tag_set.get("Value")
            
            log.info(f"Retrieved tags for object {Key} in bucket {Bucket}")
            return tags
        except Exception as e:
            log.error(f"Failed to parse tags for object {Key}: {e}")
            return {}
    else:
        log.error(f"Failed to get tags for object {Key}: {response.text}")
        return {}