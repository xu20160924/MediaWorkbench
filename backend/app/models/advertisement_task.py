from datetime import datetime
from enum import Enum
from app.extensions import db


class TaskType(Enum):
    """Task type classification"""
    normal = 'normal'
    community_special = 'community_special'


class TaskStatus(Enum):
    """Status of the advertisement task"""
    active = 'active'
    completed = 'completed'
    expired = 'expired'
    draft = 'draft'
    
    # Allow case-insensitive mapping from database values
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return super()._missing_(value)


class AdvertisementTask(db.Model):
    """Model for storing advertisement tasks from Xiaohongshu"""
    __tablename__ = 'advertisement_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Task identification
    task_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    
    # Task titles
    task_title = db.Column(db.String(500), nullable=False)
    card_title = db.Column(db.String(500))
    
    # Task rules and requirements
    submission_rules = db.Column(db.Text)
    tag_require = db.Column(db.Text)
    settlement_way = db.Column(db.Text)
    
    # Hashtags - stored as JSON array for easy use in prompts
    hashtags = db.Column(db.JSON)
    
    # Image handling - stores relative path from default location
    # Crawler should save to: <default_location>/image_path
    image_path = db.Column(db.String(500))  # Relative path from default location
    image_url = db.Column(db.String(1000))  # For external URLs (fallback)
    
    # Financial information
    ads_pool_amount = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Task status and metadata
    status = db.Column(
        db.Enum(TaskStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=TaskStatus.active,
        nullable=False
    )
    
    # Task type classification (community special vs normal)
    task_type = db.Column(
        db.Enum(TaskType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=TaskType.normal,
        nullable=False
    )
    
    # Extra data from API responses (stored as JSON for flexibility)
    extra_data = db.Column(db.JSON)
    
    # Participation tracking - stores which tasks have been processed
    participated = db.Column(db.Boolean, default=False)
    participation_count = db.Column(db.Integer, default=0)
    last_participated_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Task deadline (if available from API)
    deadline = db.Column(db.DateTime)
    
    def to_dict(self, include_rule_cards=True):
        """Convert model to dictionary"""
        # Get image info - prefer local path over external URL
        image_data = None
        if self.image_path:
            image_data = {
                'path': self.image_path,
                'url': f'/api/advertisement-tasks/image/{self.id}',  # Serve via API
                'external': False
            }
        elif self.image_url:
            image_data = {
                'url': self.image_url,
                'external': True
            }
        
        result = {
            'id': self.id,
            'task_id': self.task_id,
            'task_title': self.task_title,
            'card_title': self.card_title,
            'submission_rules': self.submission_rules,
            'tag_require': self.tag_require,
            'settlement_way': self.settlement_way,
            'hashtags': self.hashtags or [],
            'image_path': self.image_path,
            'image_url': self.image_url,
            'image': image_data,
            'ads_pool_amount': float(self.ads_pool_amount) if self.ads_pool_amount else 0.00,
            'status': self.status.value if hasattr(self.status, 'value') else self.status,
            'task_type': self.task_type.value if hasattr(self.task_type, 'value') else self.task_type,
            'participated': self.participated or False,
            'participation_count': self.participation_count or 0,
            'last_participated_at': self.last_participated_at.isoformat() if self.last_participated_at else None,
            'extra_data': self.extra_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
        }
        
        # Include rule cards if requested (sorted by display_order)
        if include_rule_cards and hasattr(self, 'rule_cards'):
            result['rule_cards'] = [rc.to_dict() for rc in sorted(self.rule_cards, key=lambda x: x.display_order)]
            result['rule_cards_count'] = len(self.rule_cards)
            result['available_rule_cards_count'] = sum(1 for rc in self.rule_cards if not rc.participated)
        
        return result
    
    @classmethod
    def from_api_data(cls, data):
        """Create instance from API response data"""
        return cls(
            task_id=data.get('taskNo'),
            task_title=data.get('taskTitle'),
            card_title=data.get('cardTitle'),
            submission_rules=data.get('submissionRules'),
            tag_require=data.get('hashtagRequirements'),
            settlement_way=data.get('settlementMethod'),
            hashtags=data.get('hashtags', []),
            image_path=data.get('imagePath'),  # Relative path where crawler saved the image
            image_url=data.get('imageUrl'),  # External URL fallback
            ads_pool_amount=data.get('bonusPoolAmount', 0),
            extra_data=data  # Store entire API response for reference
        )
    
    def __repr__(self):
        return f'<AdvertisementTask {self.task_id}: {self.task_title}>'
