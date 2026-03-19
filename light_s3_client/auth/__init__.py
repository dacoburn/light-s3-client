"""
Authentication-related operations for the light-s3-client.
This module contains functions for AWS signature creation and authentication.
Supports AWS Signature Version 2 and Version 4 (default).
"""

import base64
import hmac
from hashlib import sha256
from datetime import datetime, timezone
from urllib.parse import urlparse, quote
from ..version import __version__


def create_aws_signature(self, method, url, headers, payload=None) -> dict:
    """
    Create AWS signature and return auth headers to merge into the request.
    Dispatches to V2 or V4 based on self.signature_version.

    Args:
        method (str): HTTP method (GET, PUT, DELETE, HEAD, POST)
        url (str): Full request URL (including query string)
        headers (dict): Current request headers (User-Agent, Content-Type, etc.)
        payload: Request body (bytes, file-like object, str, or None)

    Returns:
        dict: Auth headers to merge into the request headers
    """
    if self.signature_version == "v2":
        return _create_v2_signature(self, method, url)
    else:
        return _create_v4_signature(self, method, url, payload)


def _create_v2_signature(self, method, url) -> dict:
    """Create AWS Signature Version 2 (legacy)."""
    parsed = urlparse(url)
    resource_path = parsed.path
    date = _get_current_date(self)
    string_to_sign = f"{method}\n\n\n{date}\n{resource_path}".encode("UTF-8")
    sig = base64.encodebytes(
        hmac.new(
            self.secret_key.encode("UTF-8"), string_to_sign, sha256
        ).digest()
    ).strip()
    return {
        "Authorization": f"AWS {self.access_key}:{sig.decode()}",
        "Date": date,
    }


def _create_v4_signature(self, method, url, payload=None) -> dict:
    """Create AWS Signature Version 4."""
    parsed = urlparse(url)

    # Host header value (include port for non-standard ports)
    host = parsed.hostname
    if parsed.port and parsed.port not in (80, 443):
        host = f"{parsed.hostname}:{parsed.port}"

    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    # Determine payload hash
    if payload is None:
        payload_hash = sha256(b"").hexdigest()
    elif isinstance(payload, (bytes, bytearray)):
        payload_hash = sha256(payload).hexdigest()
    elif isinstance(payload, str):
        payload_hash = sha256(payload.encode("utf-8")).hexdigest()
    else:
        # Streaming body (file-like objects) — use unsigned payload
        payload_hash = "UNSIGNED-PAYLOAD"

    # Headers to sign
    signing_headers = {
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }

    # Canonical URI
    canonical_uri = quote(parsed.path, safe="/")
    if not canonical_uri:
        canonical_uri = "/"

    # Canonical query string (handle params with and without values)
    canonical_querystring = _build_canonical_querystring(parsed.query)

    # Canonical headers and signed headers
    sorted_header_keys = sorted(signing_headers.keys())
    canonical_headers = ""
    for key in sorted_header_keys:
        canonical_headers += f"{key}:{signing_headers[key]}\n"
    signed_headers = ";".join(sorted_header_keys)

    # Canonical request
    canonical_request = (
        f"{method}\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )

    # Credential scope
    credential_scope = f"{date_stamp}/{self.region}/s3/aws4_request"

    # String to sign
    string_to_sign = (
        f"AWS4-HMAC-SHA256\n"
        f"{amz_date}\n"
        f"{credential_scope}\n"
        f"{sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    # Signing key
    signing_key = _get_v4_signing_key(self.secret_key, date_stamp, self.region, "s3")

    # Signature
    signature = hmac.new(
        signing_key,
        string_to_sign.encode("utf-8"),
        sha256
    ).hexdigest()

    # Authorization header
    authorization = (
        f"AWS4-HMAC-SHA256 "
        f"Credential={self.access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    return {
        "Authorization": authorization,
        "X-Amz-Date": amz_date,
        "X-Amz-Content-SHA256": payload_hash,
    }


def _build_canonical_querystring(query):
    """Parse and canonicalize a query string for V4 signing.
    Handles params with and without values (e.g. ?uploads, ?tagging)."""
    if not query:
        return ""
    params = []
    for part in query.split("&"):
        if "=" in part:
            key, value = part.split("=", 1)
            params.append((key, value))
        else:
            params.append((part, ""))
    params.sort(key=lambda x: (x[0], x[1]))
    return "&".join(
        f"{quote(k, safe='')}={quote(v, safe='')}" for k, v in params
    )


def _get_v4_signing_key(secret_key, date_stamp, region, service):
    """Derive the signing key for AWS Signature Version 4."""
    k_date = hmac.new(
        f"AWS4{secret_key}".encode("utf-8"),
        date_stamp.encode("utf-8"),
        sha256
    ).digest()
    k_region = hmac.new(k_date, region.encode("utf-8"), sha256).digest()
    k_service = hmac.new(k_region, service.encode("utf-8"), sha256).digest()
    k_signing = hmac.new(k_service, b"aws4_request", sha256).digest()
    return k_signing


def _get_current_date(self):
    """
    Get the current date in RFC 2822 format for V2 signatures.

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