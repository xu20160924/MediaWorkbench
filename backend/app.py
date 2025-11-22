import os
from app import create_app
from app.extensions import db
from app.scheduler import scheduler
from conf import DATABASE_URI

# --- Database Initialization for SQLite ---
# Ensure instance folder and SQLite file exist with correct permissions
# (Only needed for SQLite, MySQL manages its own files)
if 'sqlite' in DATABASE_URI.lower():
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    db_path = os.path.join(instance_path, 'app.db')
    
    if not os.path.exists(instance_path):
        print(f"Creating instance folder at: {instance_path}")
        os.makedirs(instance_path)
    
    if not os.path.exists(db_path):
        print(f"Database not found. Creating a new one at: {db_path}")
        open(db_path, 'a').close()
    
    print(f"Setting write permissions on {db_path}")
    os.chmod(db_path, 0o666)

# Create Flask app (db is already initialized inside create_app)
app = create_app()

# Create tables within the application context
with app.app_context():
    db.create_all()

# Initialize scheduler with app
scheduler.init_app(app)

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5001'))
    app.run(debug=False, host='0.0.0.0', port=port)