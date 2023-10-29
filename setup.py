import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="light-s3-client",
    version="0.0.4",
    author="Douglas Coburn",
    author_email="douglas@dactbc.com",
    description="A lightweight S3 client that does not rely on boto3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dacoburn/light-s3-client",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)