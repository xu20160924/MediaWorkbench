from datetime import datetime
from enum import Enum
from app.extensions import db

class ImageSource(Enum):
    upload = 'upload'
    local_dir = 'local_dir'
    generated = 'generated'

class ImageType(Enum):
    general = 'general'
    advertising = 'advertising_campaign'
    advertising_rule = 'advertising_rule'
    rule_card_screenshot = 'rule_card_screenshot'

    # Allow case-insensitive mapping from database values
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return super()._missing_(value)

class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    workflow_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(255), nullable=False)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'))
    variables = db.Column(db.JSON)
    source = db.Column(
        db.Enum(ImageSource, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=ImageSource.upload,
        nullable=False
    )
    image_type = db.Column(
        db.Enum(ImageType, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=ImageType.general,
        nullable=False
    )
    local_path = db.Column(db.String(500), nullable=True)  # Only used when source is LOCAL_DIR
    
    # 修改关系定义，指定正确的表名
    workflow = db.relationship('Workflow', 
                             backref=db.backref('images', lazy=True),
                              foreign_keys=[workflow_id])

    def to_dict(self):
        import os
        
        # Calculate file size from actual file
        size = 0
        for path in [self.local_path, self.file_path]:
            if path and os.path.isfile(path):
                try:
                    size = os.path.getsize(path)
                    break
                except:
                    pass
        
        return {
            'id': self.id,
            'filename': self.filename,
            'workflow_name': self.workflow_name,
            'workflow_id': self.workflow_id,
            'created_at': self.created_at.isoformat(),
            'file_path': self.file_path,
            'variables': self.variables,
            'source': self.source.value if hasattr(self.source, 'value') else self.source,
            'image_type': self.image_type.value if hasattr(self.image_type, 'value') else self.image_type,
            'local_path': self.local_path,
            'participated': (self.variables or {}).get('participated', False),
            'used': (self.variables or {}).get('used', False),
            'size': size
        }

# 默认目录配置，用于为不同图片类型设置本地扫描目录
class ImageDefaultLocation(db.Model):
    __tablename__ = 'image_default_locations'

    id = db.Column(db.Integer, primary_key=True)
    image_type = db.Column(db.String(50), nullable=False, unique=True)
    directory = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'image_type': self.image_type,
            'directory': self.directory,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }