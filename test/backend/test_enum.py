from enum import Enum
from sqlalchemy import create_engine, Column, Integer, String, Enum as SAEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create a test enum
class TestEnum(Enum):
    UPLOAD = 'upload'
    LOCAL_DIR = 'local_dir'
    GENERATED = 'generated'

# Create SQLAlchemy engine and base
engine = create_engine('sqlite:///test.db')
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Define a test model
class TestModel(Base):
    __tablename__ = 'test'
    id = Column(Integer, primary_key=True)
    status = Column(SAEnum(TestEnum, native_enum=False, values_callable=lambda x: [e.value for e in x]))

# Create tables
Base.metadata.create_all(bind=engine)

# Test inserting and querying
session = SessionLocal()

# Insert a record with enum value 'upload'
test1 = TestModel(status='upload')
session.add(test1)
session.commit()
session.refresh(test1)
print(f"Inserted record with status: {test1.status}")

# Query all records
tests = session.query(TestModel).all()
print(f"Query results: {[test.status for test in tests]}")

# Now let's try with the member directly
test2 = TestModel(status=TestEnum.LOCAL_DIR)
session.add(test2)
session.commit()
session.refresh(test2)
print(f"Inserted record with status: {test2.status}")

# Query all records again
tests = session.query(TestModel).all()
print(f"Query results: {[test.status for test in tests]}")

# Clean up
session.close()
engine.dispose()
import os
os.remove('test.db')