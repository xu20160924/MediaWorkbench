"""System configuration model for storing general system settings"""
from app.extensions import db
from datetime import datetime
import json


class SystemConfig(db.Model):
    """
    Flexible system configuration table for storing key-value settings.
    
    This table can store various types of system data:
    - Image default locations (legacy, can migrate from image_default_locations)
    - API configurations (endpoints, timeouts, retry settings)
    - Feature flags (enable/disable features)
    - System limits (max file size, rate limits)
    - UI preferences (default themes, page sizes)
    - Integration settings (external service configs)
    """
    __tablename__ = 'system_configs'

    id = db.Column(db.Integer, primary_key=True)
    
    # Category for grouping related settings
    category = db.Column(db.String(50), nullable=False, index=True)
    # e.g., 'image_locations', 'api_settings', 'feature_flags', 'limits', 'ui_defaults'
    
    # Unique key within the category
    key = db.Column(db.String(100), nullable=False, index=True)
    # e.g., 'advertising_campaign_directory', 'api_timeout', 'enable_participation', 'max_file_size'
    
    # Value stored as JSON for flexibility
    value = db.Column(db.Text, nullable=False)
    # Can store strings, numbers, arrays, objects
    
    # Data type hint for validation
    data_type = db.Column(db.String(20), default='string')
    # 'string', 'integer', 'float', 'boolean', 'json', 'array'
    
    # Human-readable description
    description = db.Column(db.String(500))
    
    # Is this setting editable by users?
    is_editable = db.Column(db.Boolean, default=True)
    
    # Is this setting visible in UI?
    is_visible = db.Column(db.Boolean, default=True)
    
    # Validation rules (optional, stored as JSON)
    validation_rules = db.Column(db.Text)
    # e.g., {"min": 0, "max": 100, "pattern": "^[a-z]+$"}
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.String(100))  # User who created this setting
    updated_by = db.Column(db.String(100))  # User who last updated
    
    # Unique constraint on category + key
    __table_args__ = (
        db.UniqueConstraint('category', 'key', name='unique_category_key'),
        db.Index('idx_category_key', 'category', 'key'),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'category': self.category,
            'key': self.key,
            'value': self.get_parsed_value(),
            'raw_value': self.value,
            'data_type': self.data_type,
            'description': self.description,
            'is_editable': self.is_editable,
            'is_visible': self.is_visible,
            'validation_rules': json.loads(self.validation_rules) if self.validation_rules else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
        }

    def get_parsed_value(self):
        """Parse value based on data_type"""
        if not self.value:
            return None
            
        try:
            if self.data_type == 'integer':
                return int(self.value)
            elif self.data_type == 'float':
                return float(self.value)
            elif self.data_type == 'boolean':
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.data_type in ('json', 'array'):
                return json.loads(self.value)
            else:  # string
                return self.value
        except (ValueError, json.JSONDecodeError):
            return self.value

    def set_value(self, value):
        """Set value with automatic serialization"""
        if self.data_type in ('json', 'array'):
            self.value = json.dumps(value, ensure_ascii=False)
        else:
            self.value = str(value)

    @classmethod
    def get(cls, category, key, default=None):
        """
        Get a configuration value
        
        Args:
            category: Configuration category
            key: Configuration key
            default: Default value if not found
            
        Returns:
            Parsed configuration value or default
        """
        config = cls.query.filter_by(category=category, key=key).first()
        if config:
            return config.get_parsed_value()
        return default

    @classmethod
    def set(cls, category, key, value, data_type='string', description=None, user=None):
        """
        Set a configuration value
        
        Args:
            category: Configuration category
            key: Configuration key
            value: Value to set
            data_type: Type of the value
            description: Human-readable description
            user: User making the change
            
        Returns:
            SystemConfig instance
        """
        config = cls.query.filter_by(category=category, key=key).first()
        
        if config:
            # Update existing
            config.set_value(value)
            config.data_type = data_type
            if description:
                config.description = description
            config.updated_by = user
            config.updated_at = datetime.utcnow()
        else:
            # Create new
            config = cls(
                category=category,
                key=key,
                data_type=data_type,
                description=description,
                created_by=user,
                updated_by=user
            )
            config.set_value(value)
            db.session.add(config)
        
        db.session.commit()
        return config

    @classmethod
    def get_category(cls, category):
        """Get all configurations in a category"""
        configs = cls.query.filter_by(category=category).all()
        return {config.key: config.get_parsed_value() for config in configs}

    def __repr__(self):
        return f'<SystemConfig {self.category}.{self.key}={self.value}>'


# Predefined system configuration categories and keys
class ConfigCategory:
    """Configuration categories"""
    IMAGE_LOCATIONS = 'image_locations'
    API_SETTINGS = 'api_settings'
    FEATURE_FLAGS = 'feature_flags'
    SYSTEM_LIMITS = 'system_limits'
    UI_DEFAULTS = 'ui_defaults'
    INTEGRATIONS = 'integrations'
    NOTIFICATIONS = 'notifications'


# Example configurations that should be initialized
DEFAULT_CONFIGS = [
    # Image locations
    {
        'category': ConfigCategory.IMAGE_LOCATIONS,
        'key': 'advertising_campaign_directory',
        'value': '/tmp/mediaworkbench/advertising_images',
        'data_type': 'string',
        'description': '广告活动图片的默认存储目录',
        'is_editable': True,
        'is_visible': True,
    },
    {
        'category': ConfigCategory.IMAGE_LOCATIONS,
        'key': 'general_directory',
        'value': '/tmp/mediaworkbench/general_images',
        'data_type': 'string',
        'description': '普通图片的默认存储目录',
        'is_editable': True,
        'is_visible': True,
    },
    {
        'category': ConfigCategory.IMAGE_LOCATIONS,
        'key': 'rule_directory',
        'value': '/tmp/mediaworkbench/rule_images',
        'data_type': 'string',
        'description': '规则图片的默认存储目录',
        'is_editable': True,
        'is_visible': True,
    },
    
    # API settings
    {
        'category': ConfigCategory.API_SETTINGS,
        'key': 'api_timeout',
        'value': '30',
        'data_type': 'integer',
        'description': 'API请求超时时间（秒）',
        'is_editable': True,
        'is_visible': True,
        'validation_rules': '{"min": 5, "max": 300}',
    },
    {
        'category': ConfigCategory.API_SETTINGS,
        'key': 'max_retry_attempts',
        'value': '3',
        'data_type': 'integer',
        'description': 'API失败重试次数',
        'is_editable': True,
        'is_visible': True,
        'validation_rules': '{"min": 0, "max": 10}',
    },
    
    # Feature flags
    {
        'category': ConfigCategory.FEATURE_FLAGS,
        'key': 'enable_task_participation',
        'value': 'true',
        'data_type': 'boolean',
        'description': '是否启用任务参与功能',
        'is_editable': True,
        'is_visible': True,
    },
    {
        'category': ConfigCategory.FEATURE_FLAGS,
        'key': 'enable_ai_generation',
        'value': 'true',
        'data_type': 'boolean',
        'description': '是否启用AI内容生成',
        'is_editable': True,
        'is_visible': True,
    },
    
    # System limits
    {
        'category': ConfigCategory.SYSTEM_LIMITS,
        'key': 'max_upload_size_mb',
        'value': '50',
        'data_type': 'integer',
        'description': '最大上传文件大小（MB）',
        'is_editable': True,
        'is_visible': True,
        'validation_rules': '{"min": 1, "max": 1000}',
    },
    {
        'category': ConfigCategory.SYSTEM_LIMITS,
        'key': 'max_images_per_task',
        'value': '100',
        'data_type': 'integer',
        'description': '每个任务最多可选择的图片数量',
        'is_editable': True,
        'is_visible': True,
        'validation_rules': '{"min": 1, "max": 1000}',
    },
    
    # UI defaults
    {
        'category': ConfigCategory.UI_DEFAULTS,
        'key': 'default_page_size',
        'value': '20',
        'data_type': 'integer',
        'description': '列表默认每页显示数量',
        'is_editable': True,
        'is_visible': True,
        'validation_rules': '{"min": 10, "max": 100}',
    },
    {
        'category': ConfigCategory.UI_DEFAULTS,
        'key': 'default_theme',
        'value': 'light',
        'data_type': 'string',
        'description': '默认主题',
        'is_editable': True,
        'is_visible': True,
    },
]
