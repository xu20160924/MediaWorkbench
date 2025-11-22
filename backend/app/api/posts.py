from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import List, Dict, Optional

from app.utils.response import success_response, error_response
from app.models.image import Image
from app.extensions import db
from app.utils.logger import logger

# Create the blueprint with /api prefix
bp = Blueprint('posts', __name__, url_prefix='/api')


@bp.route('/posts/create', methods=['POST'])
def create_post():
    """Create a new post with content and images"""
    try:
        data = request.get_json()
        
        # Validate required fields
        content = data.get('content')
        if not content or not content.strip():
            return error_response('内容不能为空')
        
        regular_image_ids = data.get('regular_image_ids', [])
        advertisement_image_ids = data.get('advertisement_image_ids', [])
        
        if not regular_image_ids and not advertisement_image_ids:
            return error_response('请至少选择一张图片')
        
        # Get optional fields
        rule_image_ids = data.get('rule_image_ids', [])
        task_id = data.get('task_id')
        task_title = data.get('task_title')
        hashtags = data.get('hashtags', [])
        
        # Verify images exist
        all_image_ids = regular_image_ids + advertisement_image_ids + rule_image_ids
        images = Image.query.filter(Image.id.in_(all_image_ids)).all()
        
        if len(images) != len(all_image_ids):
            return error_response('部分图片不存在')
        
        # Mark images as participated
        for image in images:
            if not image.participated:
                image.participated = True
        
        db.session.commit()
        
        # Prepare response data
        post_data = {
            'id': f"post_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'content': content,
            'regular_images': len(regular_image_ids),
            'advertisement_images': len(advertisement_image_ids),
            'rule_images': len(rule_image_ids),
            'total_images': len(all_image_ids),
            'task_id': task_id,
            'task_title': task_title,
            'hashtags': hashtags,
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Post created successfully: {post_data['id']}")
        logger.info(f"Content length: {len(content)} chars")
        logger.info(f"Images: {len(regular_image_ids)} regular, {len(advertisement_image_ids)} advertisement")
        
        return success_response(post_data, message='发布成功')
        
    except Exception as e:
        logger.error(f"Error creating post: {str(e)}")
        db.session.rollback()
        return error_response(f'发布失败: {str(e)}')


@bp.route('/posts/list', methods=['GET'])
def list_posts():
    """List all posts (placeholder for future implementation)"""
    try:
        # This is a placeholder - you can implement actual post storage later
        return success_response({
            'posts': [],
            'total': 0
        })
    except Exception as e:
        logger.error(f"Error listing posts: {str(e)}")
        return error_response(f'获取列表失败: {str(e)}')
