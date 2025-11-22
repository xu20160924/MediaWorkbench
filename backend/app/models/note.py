from datetime import datetime
from app.extensions import db
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON


class Note(db.Model):
    """小红书笔记记录模型"""
    __tablename__ = 'notes'
    
    id = Column(Integer, primary_key=True)
    note_id = Column(String(100), unique=True, nullable=True)  # XHS note ID
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    image_paths = Column(JSON, nullable=True)  # List of image paths
    topics = Column(JSON, nullable=True)  # List of topics/hashtags
    is_private = Column(Boolean, default=False)
    user_id = Column(Integer, nullable=False)
    
    # XHS API response
    xhs_response = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    published_at = Column(DateTime, nullable=True)
    status = Column(String(50), default='draft')  # draft, published, failed
    error_message = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'note_id': self.note_id,
            'title': self.title,
            'description': self.description,
            'image_paths': self.image_paths,
            'topics': self.topics,
            'is_private': self.is_private,
            'user_id': self.user_id,
            'xhs_response': self.xhs_response,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'status': self.status,
            'error_message': self.error_message
        }
