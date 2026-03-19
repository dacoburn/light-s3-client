class S3Error(Exception):
    pass


class BucketNotFound(S3Error):
    pass


class AccessDeniedToBucket(S3Error):
    pass


class UnknownBucketError(S3Error):
    pass
