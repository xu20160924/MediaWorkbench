import os
import sys
from flask import Flask
from flask_migrate import Migrate, upgrade

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app and db
from app import create_app, db

def run_migrations():
    # Create the Flask app
    app = create_app()
    
    # Initialize Flask-Migrate
    migrate = Migrate()
    migrate.init_app(app, db)
    
    with app.app_context():
        # Run the migration
        print("Running database migrations...")
        upgrade(directory=os.path.join(os.path.dirname(__file__), 'migrations'))
        print("Migrations completed successfully!")

if __name__ == '__main__':
    run_migrations()
