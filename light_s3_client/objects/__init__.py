"""
Object-related operations for the light-s3-client.
This module contains functions for managing S3 object tags.
"""

from ..exceptions import UnknownBucketError, BucketNotFound, AccessDeniedToBucket
from ..version import __version__
import logging
import xmltodict

log = logging.getLogger("light-s3-client")


def put_object_tagging(self, Bucket: str, Key: str, Tags: dict) -> bool:
    """
    Set tags for an S3 object.
    
    Args:
        Bucket (str): The name of the bucket
        Key (str): The key of the object to tag
        Tags (dict): Dictionary of tag key-value pairs
        
    Returns:
        bool: True if successful, False otherwise
    """
    s3_url, s3_key = self.build_vars(Key, Bucket)
    
    # Create XML for tags
    tag_xml = "<Tagging><TagSet>"
    for key, value in Tags.items():
        tag_xml += f"<Tag><Key>{key}</Key><Value>{value}</Value></Tag>"
    tag_xml += "</TagSet></Tagging>"
    
    tag_url = f"{s3_url}?tagging"
    headers = {
        "User-Agent": f"light-s3-client/{__version__}",
        "Content-Type": "application/xml"
    }
    auth_headers = self.create_aws_signature("PUT", tag_url, headers, tag_xml)
    headers.update(auth_headers)
    
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
    Retrieve tags for an S3 object.
    
    Args:
        Bucket (str): The name of the bucket
        Key (str): The key of the object to retrieve tags for
        
    Returns:
        dict: Dictionary of tag key-value pairs
    """
    s3_url, s3_key = self.build_vars(Key, Bucket)
    
    tag_url = f"{s3_url}?tagging"
    headers = {
        "User-Agent": f"light-s3-client/{__version__}"
    }
    auth_headers = self.create_aws_signature("GET", tag_url, headers)
    headers.update(auth_headers)
    
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