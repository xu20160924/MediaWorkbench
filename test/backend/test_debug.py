import sys
import os
import traceback

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from app.models.image import Image, ImageSource

# Create and configure the app the same way as in app.py
app = create_app()

# Set the correct database URI (should match conf.py)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

# Test the database connection and querying
with app.app_context():
    try:
        print("Testing database connection...")
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Test if we can query the images table
        print("Querying images...")
        images = db.session.query(Image).all()
        print(f"Found {len(images)} images")
        
        # Print details of each image
        for image in images:
            print(f"\nImage ID: {image.id}")
            print(f"Filename: {image.filename}")
            print(f"Source: {image.source}")
            print(f"Source type: {type(image.source)}")
            print(f"Source value: {image.source.value}")
            print(f"Is upload: {image.source == ImageSource.upload}")
        
        # Test enum conversion
        print("\n--- Testing enum conversion ---\n")
        print("ImageSource:", ImageSource)
        print("ImageSource.upload:", ImageSource.upload)
        print("ImageSource.upload.value:", ImageSource.upload.value)
        print("ImageSource('upload'):", ImageSource('upload'))
        print("ImageSource['upload']:", ImageSource['upload'])
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        db.session.close()