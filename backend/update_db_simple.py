import sqlite3

def update_database():
    # Connect to the SQLite database
    conn = sqlite3.connect('instance/app.db')
    cursor = conn.cursor()
    
    try:
        # Check if source column exists
        cursor.execute("""
            SELECT name FROM pragma_table_info('images') 
            WHERE name = 'source';
        """)
        
        if not cursor.fetchone():
            print("Adding 'source' column to images table...")
            cursor.execute("""
                ALTER TABLE images 
                ADD COLUMN source TEXT NOT NULL DEFAULT 'upload';
            """)
        
        # Check if local_path column exists
        cursor.execute("""
            SELECT name FROM pragma_table_info('images') 
            WHERE name = 'local_path';
        """)
        
        if not cursor.fetchone():
            print("Adding 'local_path' column to images table...")
            cursor.execute("""
                ALTER TABLE images 
                ADD COLUMN local_path TEXT;
            """)
        
        # Commit changes
        conn.commit()
        print("Database schema updated successfully.")
        
    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database()
