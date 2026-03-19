# Development Testing Information

This document contains information about testing for developers working on the light-s3-client library.

## Running Tests

To run all tests, you can use the following methods:

1. Run all tests using pytest directly:
   ```bash
   pytest tests/
   ```

2. Run the test runner script:
   ```bash
   python run_tests.py
   ```

3. For integration testing, you'll need to set up a test environment with S3 credentials or use the provided Docker Compose setup for MinIO testing:
   ```bash
   docker-compose up -d
   ```

## Test Structure

Unit tests are located in `tests/test_unit.py` and integration tests in `tests/test_integration.py`. The tests include mock testing capabilities to enable offline testing without a real S3 connection.

## Development Setup

For development, you can install the development dependencies with:
```bash
pip install -e .[dev]
```

This will install pytest, pytest-cov, black, flake8, and python-dotenv which are needed for development and testing.