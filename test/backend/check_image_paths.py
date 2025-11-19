import os
from dotenv import load_dotenv
from conf import DATABASE_URI

# Load environment variables
load_dotenv()

# Create application context
from app import create_app
from app.extensions import db
from app.models.image import Image

app = create_app()

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

with app.app_context():
    # Query all advertisement campaign images
    ad_images = Image.query.filter_by(image_type='advertising_campaign').all()
    print(f"Found {len(ad_images)} advertisement campaign images")
    
    for img in ad_images:
        print(f"ID: {img.id}")
        print(f"Filename: {img.filename}")
        print(f"File path: {img.file_path}")
        print(f"Local path: {img.local_path}")
        print(f"Image type: {img.image_type}")
        print(f"Source: {img.source}")
        print(f"Created at: {img.created_at}")
        print()
        
        # Check if file exists locally
        if os.path.exists(img.local_path):
            print(f"✓ Local file exists: {img.local_path}")
        else:
            print(f"✗ Local file not found: {img.local_path}")
        print("="*50)
        print()