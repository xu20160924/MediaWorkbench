#!/usr/bin/env python3
import sys
import os

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Set the correct app configuration
os.environ['FLASK_CONFIG'] = 'development'

from app import create_app
from app.extensions import db
from app.models.image import Image

def test_list_images():
    # Create the app with the correct configuration
    app = create_app()
    
    with app.app_context():
        try:
            # Test a simple query to count the number of images
            count = Image.query.count()
            print(f'Number of images: {count}')
            print(f'Database URI: {app.config["SQLALCHEMY_DATABASE_URI"]}')
            
            # Try to get the first image
            first_image = Image.query.first()
            if first_image:
                print(f'First image details:')
                print(f'  ID: {first_image.id}')
                print(f'  Filename: {first_image.filename}')
                print(f'  Source: {first_image.source}')
                print(f'  Source value: {first_image.source.value}')
                print(f'  Image type: {first_image.image_type}')
                print(f'  Image type value: {first_image.image_type.value}')
                
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_list_images()