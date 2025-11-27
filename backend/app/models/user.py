from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    nickname = db.Column(db.String(100), nullable=True)
    cookie = db.Column(db.Text, nullable=False)
    session_id = db.Column(db.String(200), nullable=True)  # XHS session ID
    status = db.Column(db.Boolean, default=True)  # True for active, False for inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'cookie': self.cookie,  # Include cookie for editing
            'session_id': self.session_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }