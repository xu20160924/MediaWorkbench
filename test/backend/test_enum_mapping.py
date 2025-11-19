#!/usr/bin/env python3
import enum
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Define the enum class
class ImageSource(enum.Enum):
    UPLOAD = 'upload'
    LOCAL_DIR = 'local_dir'
    GENERATED = 'generated'

# Create engine
engine = create_engine('sqlite:///:memory:')

# Create a table with the enum column
class TestImage(Base):
    __tablename__ = 'test_images'
    id = sa.Column(sa.Integer, primary_key=True)
    filename = sa.Column(sa.String(255))
    source = sa.Column(
        sa.Enum(ImageSource, native_enum=False, by_value=True, values_callable=lambda x: [e.value for e in x]),
        default=ImageSource.UPLOAD,
        nullable=False
    )

# Create all tables
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()

# Test inserting with enum member
print("Inserting with enum member...")
img1 = TestImage(filename='test1.jpg', source=ImageSource.UPLOAD)
session.add(img1)
session.commit()

# Test inserting with string value
print("Inserting with string value...")
img2 = TestImage(filename='test2.jpg', source='local_dir')
session.add(img2)
session.commit()

# Query and print results
print("Querying all images...")
images = session.query(TestImage).all()
for img in images:
    print(f"ID: {img.id}, Filename: {img.filename}, Source: {img.source}, Source type: {type(img.source)}")

# Let's also check what's in the _object_lookup
print("\nChecking enum type object lookup...")
enum_type = TestImage.__table__.columns['source'].type
print(f"Enum type: {enum_type}")
print(f"Enum values_callable: {enum_type.values_callable}")
print(f"Enum by_value: {getattr(enum_type, 'by_value', 'N/A')}")
print(f"Enum _object_lookup: {enum_type._object_lookup}")
print(f"Enum _member_map_: {ImageSource._member_map_}")
print(f"Enum values: {[e.value for e in ImageSource]}")

# Test with actual database values
print("\nQuerying with filter using enum member...")
img_upload = session.query(TestImage).filter_by(source=ImageSource.UPLOAD).first()
if img_upload:
    print(f"Found image: {img_upload.filename}, Source: {img_upload.source}")

print("Querying with filter using string value...")
img_local = session.query(TestImage).filter_by(source='local_dir').first()
if img_local:
    print(f"Found image: {img_local.filename}, Source: {img_local.source}")

# Cleanup
session.close()