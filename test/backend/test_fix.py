from app import create_app
from app.models.image import Image

# Create and configure app
app = create_app()

with app.app_context():
    try:
        # Test querying all images
        images = Image.query.all()
        print(f"Success! Found {len(images)} images.")
        
        # Test a specific image
        if images:
            image = images[0]
            print(f"First image: ID={image.id}, Filename={image.filename}, Source={image.source}")
            print(f"Source type: {type(image.source)}")
            print(f"Source value: {image.source.value}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()