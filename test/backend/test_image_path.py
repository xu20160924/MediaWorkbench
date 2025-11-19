import os
import sys

# Add the backend directory to the Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_dir)

from conf import UPLOAD_FOLDER

# Test with a specific filename
filename = 'text-to-image-workflow.png'

print(f"UPLOAD_FOLDER: {UPLOAD_FOLDER}")
print(f"Checking if file exists at: {os.path.join(UPLOAD_FOLDER, filename)}")
print(f"File exists: {os.path.exists(os.path.join(UPLOAD_FOLDER, filename))}")

# Let's also check what the static.py route would do
frontend_request_filename = f"upload/{filename}"
print(f"\nFrontend request would be: /images/{frontend_request_filename}")
print(f"static.py serve_image would process filename: {frontend_request_filename}")
print(f"It would remove 'upload/' prefix to get: {frontend_request_filename[7:]}")
print(f"Then look for file at: {os.path.join(UPLOAD_FOLDER, frontend_request_filename[7:])}")
print(f"File exists: {os.path.exists(os.path.join(UPLOAD_FOLDER, frontend_request_filename[7:]))}")