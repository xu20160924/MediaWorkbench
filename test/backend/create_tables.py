from app import create_app
from app.extensions import db
from app.models.image import Image, ImageSource, ImageType

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db.init_app(app)  # Initialize the db extension with the app

with app.app_context():
    db.create_all()
    print("Database tables created successfully.")