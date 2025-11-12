import os
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from conf import DATABASE_URI

def init_db():
    print("Initializing database...")
    
    # Create engine and connect to the database
    engine = create_engine(DATABASE_URI)
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create tables if they don't exist
    metadata = MetaData()
    
    # Create workflows table if it doesn't exist
    Table('workflows', metadata,
        Column('id', Integer, primary_key=True),
        Column('name', String(255), nullable=False),
        Column('description', String(500)),
        Column('file_path', String(500), nullable=False),
        Column('created_at', DateTime, nullable=False),
        Column('updated_at', DateTime, nullable=False),
        Column('input_vars', JSON),
        Column('output_vars', JSON)
    )
    
    # Create images table with the new columns
    Table('images', metadata,
        Column('id', Integer, primary_key=True),
        Column('filename', String(255), nullable=False),
        Column('workflow_name', String(255)),
        Column('created_at', DateTime, nullable=False),
        Column('file_path', String(500), nullable=False),
        Column('workflow_id', Integer, ForeignKey('workflows.id')),
        Column('variables', JSON),
        Column('source', String(20), nullable=False, server_default='upload'),
        Column('local_path', String(500))
    )
    
    # Create other necessary tables
    Table('variable_definitions', metadata,
        Column('id', Integer, primary_key=True),
        Column('class_type', String(255), nullable=False),
        Column('value_path', String(255), nullable=False),
        Column('value_type', String(50), nullable=False),
        Column('param_type', String(50), nullable=False),
        Column('description', String(500))
    )
    
    Table('workflow_variables', metadata,
        Column('id', Integer, primary_key=True),
        Column('workflow_id', Integer, ForeignKey('workflows.id'), nullable=False),
        Column('node_id', String(100), nullable=False),
        Column('class_type_id', Integer, ForeignKey('variable_definitions.id'), nullable=False),
        Column('title', String(255))
    )
    
    # Create all tables
    print("Creating database tables...")
    metadata.create_all(engine)
    
    # Add a check constraint for the source column (for databases that support it)
    if 'sqlite' not in DATABASE_URI:
        with engine.connect() as conn:
            conn.execute('''
                ALTER TABLE images 
                ADD CONSTRAINT chk_source 
                CHECK (source IN ('upload', 'local_dir', 'generated'))
            ''')
    
    print("Database initialization completed successfully!")
    session.close()

if __name__ == '__main__':
    init_db()
