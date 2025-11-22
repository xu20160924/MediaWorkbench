from datetime import datetime
from app.extensions import db


class TaskRuleCard(db.Model):
    """Model for storing multiple rule cards for each advertisement task"""
    __tablename__ = 'task_rule_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to advertisement task
    task_id = db.Column(db.Integer, db.ForeignKey('advertisement_tasks.id', ondelete='CASCADE'), nullable=False)
    
    # Rule card information
    rule_name = db.Column(db.String(200))  # Optional name for the rule (e.g., "规则卡片1", "活动要求A")
    rule_description = db.Column(db.Text)  # Optional description
    
    # Image handling - stores relative path from advertising_rule default location
    image_path = db.Column(db.String(500))  # Relative path from default location
    image_url = db.Column(db.String(1000))  # For external URLs (fallback)
    
    # Order for displaying multiple rules
    display_order = db.Column(db.Integer, default=0)
    
    # Participation tracking for this specific rule card
    participated = db.Column(db.Boolean, default=False)
    participation_count = db.Column(db.Integer, default=0)
    last_participated_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship back to task
    task = db.relationship('AdvertisementTask', backref=db.backref('rule_cards', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self):
        """Convert model to dictionary"""
        # Get image info - prefer local path over external URL
        image_data = None
        if self.image_path:
            image_data = {
                'path': self.image_path,
                'url': f'/api/advertisement-tasks/rule-card/{self.id}/image',  # Serve via API
                'external': False
            }
        elif self.image_url:
            image_data = {
                'url': self.image_url,
                'external': True
            }
        
        return {
            'id': self.id,
            'task_id': self.task_id,
            'rule_name': self.rule_name,
            'rule_description': self.rule_description,
            'image_path': self.image_path,
            'image_url': self.image_url,
            'image': image_data,
            'display_order': self.display_order or 0,
            'participated': self.participated or False,
            'participation_count': self.participation_count or 0,
            'last_participated_at': self.last_participated_at.isoformat() if self.last_participated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f'<TaskRuleCard {self.id} for Task {self.task_id}: {self.rule_name}>'
