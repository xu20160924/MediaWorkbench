"""Test local image storage for advertisement tasks"""
from app import create_app
from app.extensions import db
from app.models.advertisement_task import AdvertisementTask
from app.models.image import Image, ImageSource, ImageType
import os

app = create_app()

with app.app_context():
    # Step 1: Create a sample image record (simulating a crawled image)
    # In reality, you would save the actual file first
    image = Image(
        filename='ad_sample_image.jpg',
        file_path='/path/to/your/ad_images/sample.jpg',  # Your actual file path
        source=ImageSource.generated,
        image_type=ImageType.advertising  # For advertisement images
    )
    db.session.add(image)
    db.session.flush()  # Get the image ID
    
    print(f"✓ Created image record")
    print(f"  Image ID: {image.id}")
    print(f"  Filename: {image.filename}")
    
    # Step 2: Get an existing advertisement task and link it to the image
    task = AdvertisementTask.query.first()
    
    if task:
        task.image_id = image.id
        db.session.commit()
        
        print(f"\n✓ Linked image to advertisement task")
        print(f"  Task ID: {task.task_id}")
        print(f"  Task Title: {task.task_title}")
        print(f"  Image ID: {task.image_id}")
        
        # Step 3: Verify the relationship works
        task_dict = task.to_dict()
        print(f"\n✓ Task API response includes image:")
        print(f"  Image URL: {task_dict['image']['url']}")
        print(f"  Image Filename: {task_dict['image']['filename']}")
        print(f"\n  Frontend will display image from: http://localhost:5001{task_dict['image']['url']}")
        
    else:
        print("\n✗ No advertisement tasks found in database")
        print("  Create a task first using the frontend")
    
    db.session.rollback()  # Don't actually save for this test
