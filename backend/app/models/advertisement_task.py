from datetime import datetime
from enum import Enum
from app.extensions import db
from sqlalchemy import event
from sqlalchemy.orm import validates


class TaskType(Enum):
    """Task type classification"""
    submission = 'submission'  # Submission tasks (投稿活动)
    normal = 'normal'  # Legacy alias for submission
    regular = 'regular'  # Legacy alias for submission
    community = 'community'  # Community tasks (社群任务)
    community_special = 'community_special'  # Community special/SP tasks
    buyer = 'buyer'  # Buyer tasks (买手合作)
    
    # Allow case-insensitive mapping and handle legacy values
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
            # Handle legacy or alternative names
            if value_lower in ('community', 'community_task'):
                return cls.community
            if value_lower in ('regular', 'default', 'normal'):
                return cls.submission
        return super()._missing_(value)


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
    
    @validates('status')
    def validate_status(self, key, value):
        """Normalize status to lowercase to handle case-insensitive input"""
        if isinstance(value, str):
            value = value.lower()
            # Convert string to enum
            try:
                return TaskStatus(value)
            except ValueError:
                # If still invalid, return default
                return TaskStatus.active
        return value
    
    # Task type classification (community special vs normal)
    task_type = db.Column(
        db.Enum(TaskType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=TaskType.normal,
        nullable=False
    )
    
    @validates('task_type')
    def validate_task_type(self, key, value):
        """Normalize task_type to handle string values"""
        if isinstance(value, str):
            value = value.lower()
            try:
                return TaskType(value)
            except ValueError:
                # If still invalid, return default
                return TaskType.normal
        return value
    
    @staticmethod
    def classify_task_type(title: str) -> TaskType:
        """
        Classify task type based on title keywords.
        Community task keywords: 社群, 社群专属, 社群专属任务, 社群SP委托, 社群活动, 社群征集活动
        """
        if not title:
            return TaskType.normal
        
        # Community task keywords (case-insensitive for Chinese)
        community_keywords = [
            '社群专属任务',
            '社群专属',
            '社群SP委托',
            '社群征集活动',
            '社群活动',
            '社群',
        ]
        
        # Check for community keywords (order matters - more specific first)
        for keyword in community_keywords:
            if keyword in title:
                # Distinguish between regular community and special SP tasks
                if 'SP' in title or 'SP委托' in title:
                    return TaskType.community_special
                return TaskType.community
        
        return TaskType.normal
    
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
    
    # Relationship to rule cards
    rule_cards = db.relationship(
        'TaskRuleCard',
        back_populates='task',
        lazy=True,
        cascade='all, delete-orphan'
    )
    
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
        if include_rule_cards:
            try:
                if hasattr(self, 'rule_cards') and self.rule_cards is not None:
                    rule_cards_list = sorted(self.rule_cards, key=lambda x: x.display_order or 0)
                    result['rule_cards'] = [rc.to_dict() for rc in rule_cards_list]
                    result['rule_cards_count'] = len(self.rule_cards)
                    result['available_rule_cards_count'] = sum(1 for rc in self.rule_cards if not rc.participated)
                else:
                    result['rule_cards'] = []
                    result['rule_cards_count'] = 0
                    result['available_rule_cards_count'] = 0
            except Exception as e:
                # If there's any error loading rule cards, return empty list
                result['rule_cards'] = []
                result['rule_cards_count'] = 0
                result['available_rule_cards_count'] = 0
        
        return result
    
    @classmethod
    def from_api_data(cls, data):
        """Create instance from API response data"""
        task_title = data.get('taskTitle', '')
        
        # Auto-classify task type based on title keywords
        task_type = cls.classify_task_type(task_title)
        
        return cls(
            task_id=data.get('taskNo'),
            task_title=task_title,
            card_title=data.get('cardTitle'),
            submission_rules=data.get('submissionRules'),
            tag_require=data.get('hashtagRequirements'),
            settlement_way=data.get('settlementMethod'),
            hashtags=data.get('hashtags', []),
            image_path=data.get('imagePath'),  # Relative path where crawler saved the image
            image_url=data.get('imageUrl'),  # External URL fallback
            ads_pool_amount=data.get('bonusPoolAmount', 0),
            task_type=task_type,  # Auto-classified based on title
            extra_data=data  # Store entire API response for reference
        )
    
    def __repr__(self):
        return f'<AdvertisementTask {self.task_id}: {self.task_title}>'
