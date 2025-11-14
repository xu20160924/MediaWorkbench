from app import create_app
from app.extensions import db
from app.models.image import Image, ImageSource
import os
from conf import DATABASE_URI

def update_database():
    app = create_app()
    db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    with app.app_context():
        # Add the new columns if they don't exist
        with db.engine.connect() as conn:
            # Check if source column exists
            result = conn.exec_driver_sql("""
                SELECT name FROM pragma_table_info('images') 
                WHERE name = 'source';
            """).fetchone()
            
            if not result:
                print("Adding 'source' column to images table...")
                conn.exec_driver_sql("""
                    ALTER TABLE images 
                    ADD COLUMN source VARCHAR(20) NOT NULL DEFAULT 'upload';
                """)
            # Normalize source values to enum values (lowercase)
            print("Normalizing 'source' values to enum values...")
            conn.exec_driver_sql("""
                UPDATE images SET source = 'upload' WHERE UPPER(source) = 'UPLOAD';
            """)
            conn.exec_driver_sql("""
                UPDATE images SET source = 'local_dir' WHERE UPPER(source) = 'LOCAL_DIR';
            """)
            
            # Check if local_path column exists
            result = conn.exec_driver_sql("""
                SELECT name FROM pragma_table_info('images') 
                WHERE name = 'local_path';
            """).fetchone()
            
            if not result:
                print("Adding 'local_path' column to images table...")
                conn.exec_driver_sql("""
                    ALTER TABLE images 
                    ADD COLUMN local_path VARCHAR(500);
                """)

            # Check if image_type column exists
            result = conn.exec_driver_sql("""
                SELECT name FROM pragma_table_info('images') 
                WHERE name = 'image_type';
            """).fetchone()

            if not result:
                print("Adding 'image_type' column to images table...")
                conn.exec_driver_sql("""
                    ALTER TABLE images 
                    ADD COLUMN image_type VARCHAR(50) NOT NULL DEFAULT 'general';
                """)
            # Normalize image_type values to enum values (lowercase)
            print("Normalizing 'image_type' values to enum values...")
            conn.exec_driver_sql("""
                UPDATE images SET image_type = 'general' WHERE UPPER(image_type) = 'GENERAL';
            """)
            conn.exec_driver_sql("""
                UPDATE images SET image_type = 'advertising_campaign' WHERE UPPER(image_type) IN ('ADVERTISING','ADVERTISING_CAMPAIGN');
            """)
            conn.exec_driver_sql("""
                UPDATE images SET image_type = 'advertising_rule' WHERE UPPER(image_type) = 'ADVERTISING_RULE';
            """)
            
            db.session.commit()
            print("Database schema updated successfully.")

if __name__ == "__main__":
    update_database()
