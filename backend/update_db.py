from app import create_app
from app.extensions import db
from app.models.image import Image, ImageSource

def update_database():
    app = create_app()
    with app.app_context():
        # Add the new columns if they don't exist
        with db.engine.connect() as conn:
            # Check if source column exists
            result = conn.execute("""
                SELECT name FROM pragma_table_info('images') 
                WHERE name = 'source';
            """).fetchone()
            
            if not result:
                print("Adding 'source' column to images table...")
                conn.execute("""
                    ALTER TABLE images 
                    ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'upload';
                """)
            
            # Check if local_path column exists
            result = conn.execute("""
                SELECT name FROM pragma_table_info('images') 
                WHERE name = 'local_path';
            """).fetchone()
            
            if not result:
                print("Adding 'local_path' column to images table...")
                conn.execute("""
                    ALTER TABLE images 
                    ADD COLUMN local_path VARCHAR(500);
                """)
            
            db.session.commit()
            print("Database schema updated successfully.")

if __name__ == "__main__":
    update_database()
