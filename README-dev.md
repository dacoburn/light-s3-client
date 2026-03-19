# Development Testing Information

This document contains information about testing for developers working on the light-s3-client library.

## Development Setup

This project uses `uv` for dependency management. To set up the development environment:

```bash
# Install dependencies and create venv
uv sync

# Install with dev dependencies
uv sync --extra dev
```

Alternatively, you can use pip with a virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
source .venv/bin/activate

# Install dev dependencies
pip install -e ".[dev]"
```

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

## Development Dependencies

For development, install with dev extras:
```bash
uv sync --extra dev
```

Or with pip:
```bash
pip install -e ".[dev]"
```

This will install pytest, pytest-cov, black, flake8, and python-dotenv which are needed for development and testing.