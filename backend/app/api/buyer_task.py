"""API endpoints for buyer tasks"""
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.buyer_task import BuyerTask, BuyerTaskStatus
from sqlalchemy import desc
from app.utils.logger import logger

bp = Blueprint('buyer_task', __name__, url_prefix='/api/buyer-tasks')


@bp.route('/', methods=['GET'])
def get_buyer_tasks():
    """Get all buyer tasks with pagination"""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        # Build query
        query = BuyerTask.query
        
        # Filter by status if provided
        if status:
            query = query.filter_by(status=status)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(BuyerTask.created_at))
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        tasks = []
        for task in pagination.items:
            try:
                task_dict = {
                    'id': task.id,
                    'item_id': task.item_id,
                    'sku_id': task.sku_id,
                    'plan_id': task.plan_id,
                    'plan_type': task.plan_type,
                    'title': task.title,
                    'item_price': str(task.item_price) if task.item_price else None,
                    'item_income': str(task.item_income) if task.item_income else None,
                    'rate': task.rate,
                    'total_sales_volume': task.total_sales_volume,
                    'main_image_url': task.main_image_url,
                    'small_images': task.small_images,
                    'jump_url': task.jump_url,
                    'item_url': task.item_url,
                    'seller_id': task.seller_id,
                    'seller_name': task.seller_name,
                    'seller_score': task.seller_score,
                    'seller_image': task.seller_image,
                    'board_infos': task.board_infos,
                    'tag_info': task.tag_info,
                    'status': task.status,
                    'created_at': task.created_at.isoformat() if task.created_at else None,
                    'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                    'task_type': 'buyer'  # Add task_type for frontend
                }
                tasks.append(task_dict)
            except Exception as task_error:
                logger.exception("Error serializing buyer task", extra={
                    'task_id': task.id,
                    'item_id': task.item_id
                })
                raise
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': tasks,
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages
            }
        })
    except Exception as e:
        logger.exception("Failed to fetch buyer tasks", extra={
            'status_filter': status,
            'page': page,
            'per_page': per_page
        })
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/<int:task_id>', methods=['GET'])
def get_buyer_task(task_id):
    """Get a specific buyer task"""
    try:
        task = BuyerTask.query.get_or_404(task_id)
        return jsonify({
            'success': True,
            'data': {
                'id': task.id,
                'item_id': task.item_id,
                'title': task.title,
                'item_price': str(task.item_price) if task.item_price else None,
                'item_income': str(task.item_income) if task.item_income else None,
                'rate': task.rate,
                'total_sales_volume': task.total_sales_volume,
                'main_image_url': task.main_image_url,
                'small_images': task.small_images,
                'seller_name': task.seller_name,
                'seller_score': task.seller_score,
                'seller_image': task.seller_image,
                'board_infos': task.board_infos,
                'tag_info': task.tag_info,
                'jump_url': task.jump_url,
                'item_url': task.item_url,
                'list_data': task.list_data,
                'detail_data': task.detail_data,
                'status': task.status,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None
            }
        })
    except Exception as e:
        logger.exception("Failed to fetch buyer task", extra={'task_id': task_id})
        return jsonify({'success': False, 'error': str(e)}), 500
