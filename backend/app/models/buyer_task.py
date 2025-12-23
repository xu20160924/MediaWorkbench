from datetime import datetime
from enum import Enum
from app.extensions import db
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Text


class BuyerTaskStatus(Enum):
    """Status of buyer tasks"""
    active = 'active'
    inactive = 'inactive'
    
    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return super()._missing_(value)


class BuyerTask(db.Model):
    """Model for storing buyer tasks from Xiaohongshu"""
    __tablename__ = 'buyer_tasks'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.String(255), unique=True, nullable=False, index=True, comment='商品ID')
    sku_id = db.Column(db.String(255), index=True, comment='SKU ID')
    plan_id = db.Column(db.String(255), index=True, comment='计划ID')
    plan_type = db.Column(db.String(50), comment='计划类型')
    
    # Basic information
    title = db.Column(Text, nullable=False, comment='商品标题')
    item_price = db.Column(db.String(50), comment='商品价格')
    item_income = db.Column(db.String(50), comment='预估收益')
    rate = db.Column(db.Integer, comment='佣金比例(基点,如2000表示20%)')
    total_sales_volume = db.Column(db.Integer, comment='总销量')
    
    # Images
    main_image_url = db.Column(Text, comment='主图URL')
    small_images = db.Column(JSON, comment='小图数组')
    
    # URLs
    jump_url = db.Column(Text, comment='跳转链接')
    item_url = db.Column(Text, comment='商品详情链接')
    
    # Seller information
    seller_id = db.Column(db.String(255), index=True, comment='卖家ID')
    seller_name = db.Column(db.String(255), comment='店铺名称')
    seller_score = db.Column(db.Float, comment='店铺评分')
    seller_image = db.Column(Text, comment='店铺头像')
    
    # Additional details
    board_infos = db.Column(JSON, comment='标签信息')
    tag_info = db.Column(JSON, comment='Tag信息')
    
    # Status
    status = db.Column(db.String(50), default=BuyerTaskStatus.active.value, comment='任务状态')
    
    # Complete raw data from API
    list_data = db.Column(JSON, comment='买手任务列表原始数据')
    detail_data = db.Column(JSON, comment='买手任务详情原始数据')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment='更新时间')
    
    def __repr__(self):
        return f'<BuyerTask {self.item_id}: {self.title}>'
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'item_id': self.item_id,
            'sku_id': self.sku_id,
            'plan_id': self.plan_id,
            'plan_type': self.plan_type,
            'title': self.title,
            'item_price': self.item_price,
            'item_income': self.item_income,
            'rate': self.rate,
            'total_sales_volume': self.total_sales_volume,
            'main_image_url': self.main_image_url,
            'small_images': self.small_images,
            'jump_url': self.jump_url,
            'item_url': self.item_url,
            'seller_id': self.seller_id,
            'seller_name': self.seller_name,
            'seller_score': self.seller_score,
            'seller_image': self.seller_image,
            'board_infos': self.board_infos,
            'tag_info': self.tag_info,
            'status': self.status,
            'list_data': self.list_data,
            'detail_data': self.detail_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
