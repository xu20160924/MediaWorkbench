import os
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, String, Enum
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from conf import DATABASE_URI

def apply_migration():
    print("Connecting to database...")
    engine = create_engine(DATABASE_URI)
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Check if the table exists
    with engine.connect() as conn:
        inspector = engine.dialect.has_table(conn, 'images')
        if not inspector:
            print("Error: 'images' table does not exist.")
            return
    
    # Get the current table definition
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    # Check if the columns already exist
    if 'source' not in metadata.tables['images'].columns:
        print("Adding 'source' column to 'images' table...")
        # Add the 'source' column with a default value
        with engine.connect() as conn:
            # For SQLite
            if 'sqlite' in DATABASE_URI:
                # SQLite doesn't support adding a column with a default value that's not a constant
                conn.execute('ALTER TABLE images ADD COLUMN source TEXT NOT NULL DEFAULT "upload"')
                # Create a custom CHECK constraint to simulate an ENUM
                conn.execute('''
                    CREATE TEMPORARY TABLE images_temp (
                        id INTEGER NOT NULL, 
                        filename VARCHAR(255) NOT NULL, 
                        workflow_name VARCHAR(255), 
                        created_at DATETIME, 
                        file_path VARCHAR(255) NOT NULL, 
                        workflow_id INTEGER, 
                        variables JSON, 
                        source TEXT NOT NULL DEFAULT 'upload' CHECK(source IN ('upload', 'local_dir', 'generated')), 
                        local_path VARCHAR(500), 
                        PRIMARY KEY (id), 
                        FOREIGN KEY(workflow_id) REFERENCES workflows (id)
                    )
                ''')
                # Copy data from the old table to the new one
                conn.execute('''
                    INSERT INTO images_temp (id, filename, workflow_name, created_at, file_path, workflow_id, variables, source, local_path)
                    SELECT id, filename, workflow_name, created_at, file_path, workflow_id, variables, 'upload', NULL FROM images
                ''')
                # Drop the old table and rename the new one
                conn.execute('DROP TABLE images')
                conn.execute('ALTER TABLE images_temp RENAME TO images')
                print("Added 'source' column with ENUM constraint")
                
                # Now add the local_path column
                print("Adding 'local_path' column to 'images' table...")
                conn.execute('ALTER TABLE images ADD COLUMN local_path VARCHAR(500)')
                print("Added 'local_path' column")
            else:
                # For other databases like PostgreSQL
                conn.execute('''
                    ALTER TABLE images 
                    ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'upload' 
                    CHECK (source IN ('upload', 'local_dir', 'generated'))
                ''')
                conn.execute('ALTER TABLE images ADD COLUMN local_path VARCHAR(500)')
        
        print("Migration completed successfully!")
    else:
        print("The 'source' column already exists in the 'images' table.")
    
    session.close()

if __name__ == '__main__':
    apply_migration()
