import os
from app import create_app
from app.extensions import db
from conf import DATABASE_URI
from app.scheduler import scheduler
import os

# --- Database Initialization ---
# This block ensures the database file exists and has the correct permissions.

# Define the absolute path for the instance folder and the database file.
# This avoids any ambiguity with relative paths.
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
db_path = os.path.join(instance_path, 'app.db')

# Create the instance folder if it doesn't exist.
if not os.path.exists(instance_path):
    print(f"Creating instance folder at: {instance_path}")
    os.makedirs(instance_path)

# If the database file doesn't exist, create it.
if not os.path.exists(db_path):
    print(f"Database not found. Creating a new one at: {db_path}")
    # Create an empty file.
    open(db_path, 'a').close()

# Set the file permissions to be writable by everyone (owner, group, and other).
# This is a robust way to solve permission issues in a local dev environment.
print(f"Setting write permissions on {db_path}")
os.chmod(db_path, 0o666)

app = create_app()

# Ensure the instance folder exists
try:
    os.makedirs(app.instance_path)
except OSError:
    pass

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

# Create tables within the application context to ensure they exist before app runs
with app.app_context():
    db.create_all()


# Initialize scheduler with app
scheduler.init_app(app)

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5001'))
    app.run(debug=False, host='0.0.0.0', port=port)