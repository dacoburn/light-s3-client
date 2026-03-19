#!/usr/bin/env python3
"""
Test runner script for light-s3-client
"""

import subprocess
import sys
import os

def run_tests():
    """Run all tests for the light-s3-client"""
    
    print("Running light-s3-client tests...")
    
    # Run unit tests
    print("\nRunning unit tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/test_unit.py", "-v"])
    if result.returncode != 0:
        print("Unit tests failed!")
        return False
    
    # Run integration tests
    print("\nRunning integration tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/test_integration.py", "-v"])
    if result.returncode != 0:
        print("Integration tests failed!")
        return False
    
    print("\nAll tests passed!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)