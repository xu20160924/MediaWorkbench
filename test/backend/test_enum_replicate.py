#!/usr/bin/env python3
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Import the actual enum and models
from app.models.image import ImageSource, ImageType

# Test the enum directly
print("Testing enum directly...")
print(f"ImageSource: {ImageSource}")
print(f"ImageSource members: {list(ImageSource)}")
print(f"ImageSource.UPLOAD: {ImageSource.UPLOAD}")
print(f"ImageSource.UPLOAD.value: {ImageSource.UPLOAD.value}")
print(f"ImageSource['UPLOAD']: {ImageSource['UPLOAD']}")

# Test attribute access
print(f"\nTesting attribute access...")
try:
    print(f"getattr(ImageSource, 'UPLOAD'): {getattr(ImageSource, 'UPLOAD')}")
    print(f"getattr(ImageSource, 'upload'): {getattr(ImageSource, 'upload')}")  # This should fail
except AttributeError as e:
    print(f"ERROR: {e}")

# Test value mapping
print(f"\nTesting value mapping...")
try:
    # Try to find the enum member by value
    for member in ImageSource:
        print(f"  {member.value} -> {member}")
    
    # Check what happens when we try to use the value as a member name
    value = 'upload'
    print(f"\nTrying to map value '{value}' to enum member...")
    print(f"  1. By value: {[e for e in ImageSource if e.value == value]}")
    print(f"  2. By name: {ImageSource.__members__.get(value.upper())}")
    print(f"  3. By name (lower): {ImageSource.__members__.get(value.lower())}")  # This should be None
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test ImageType as well
print(f"\nTesting ImageType...")
print(f"ImageType.GENERAL: {ImageType.GENERAL}")
print(f"ImageType.GENERAL.value: {ImageType.GENERAL.value}")
print(f"ImageType.__members__: {ImageType.__members__}")