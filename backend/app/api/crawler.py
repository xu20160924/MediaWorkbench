"""
Crawler API endpoints for managing XHS advertisement task crawling.
This file provides the Flask API endpoints only.
Business logic is in spider/crawler_service.py.
"""
import logging
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

bp = Blueprint('crawler', __name__, url_prefix='/api/crawler')
logger = logging.getLogger(__name__)


def _get_service():
    """Lazy import to avoid circular imports"""
    from spider.crawler_service import get_crawler_service
    return get_crawler_service()


def _extract_credentials_from_user(user) -> dict:
    """Extract session credentials from user model"""
    cookie = user.cookie or ''
    session_token = ''
    x_signature = ''
    
    # Parse cookie to get session token
    for part in cookie.split(';'):
        part = part.strip()
        if part.startswith('web_session='):
            session_token = part.split('=', 1)[1]
        elif part.startswith('websectiga='):
            x_signature = part.split('=', 1)[1]
    
    # Use session_id if available
    if user.session_id:
        session_token = user.session_id
    
    return {
        'session_token': session_token,
        'x_signature': x_signature,
        'cookie': cookie
    }


@bp.route('/start', methods=['POST'])
@cross_origin()
def start_crawler():
    """Start the crawler with the given configuration"""
    service = _get_service()
    
    if service.is_running:
        return jsonify({
            'success': False,
            'message': '爬虫正在运行中'
        }), 400
    
    config = request.json or {}
    
    # Get user credentials by user_id
    user_id = config.get('user_id')
    if not user_id:
        return jsonify({
            'success': False,
            'message': '请选择小红书账户'
        }), 400
    
    # Fetch user from database
    try:
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '账户不存在'
            }), 404
        
        # Extract credentials
        credentials = _extract_credentials_from_user(user)
        
        if not credentials['session_token']:
            return jsonify({
                'success': False,
                'message': '账户Cookie中未找到session信息'
            }), 400
        
        # Update config with extracted credentials
        config.update(credentials)
        
        logger.info(f"Using credentials from user {user.username} (ID: {user_id})")
        logger.info(f"session_token: {len(credentials['session_token'])} chars, x_signature: {len(credentials['x_signature'])} chars")
        
        if not credentials['x_signature']:
            logger.warning("x_signature not found in cookie (websectiga). API calls may fail.")
        
        # Validate session before starting crawler
        validation_result = service.validate_session(
            credentials['session_token'], 
            credentials['x_signature']
        )
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'message': f'账户登录状态已失效: {validation_result["error"]}，请重新登录小红书'
            }), 400
        
        logger.info(f"Session validated successfully for user {user.username}")
        
    except Exception as e:
        logger.exception("Failed to get user credentials")
        return jsonify({
            'success': False,
            'message': f'获取账户信息失败: {str(e)}'
        }), 500
    
    # Clear previous logs and run crawler
    service.clear_logs()
    result = service.run_subprocess(config)
    
    # Get recent tasks from database
    recent_tasks = []
    try:
        from app.models.advertisement_task import AdvertisementTask
        tasks = AdvertisementTask.query.order_by(
            AdvertisementTask.created_at.desc()
        ).limit(10).all()
        recent_tasks = [t.to_dict(include_rule_cards=False) for t in tasks]
    except Exception as e:
        logger.warning(f"Failed to fetch recent tasks: {e}")
    
    if result.get('data'):
        result['data']['recent_tasks'] = recent_tasks
    
    return jsonify(result)


@bp.route('/stop', methods=['POST'])
@cross_origin()
def stop_crawler():
    """Stop the running crawler"""
    service = _get_service()
    result = service.stop()
    
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


@bp.route('/status', methods=['GET'])
@cross_origin()
def get_status():
    """Get the current crawler status"""
    service = _get_service()
    
    return jsonify({
        'success': True,
        'data': service.get_status()
    })


@bp.route('/logs', methods=['GET'])
@cross_origin()
def get_logs():
    """Get crawler logs"""
    service = _get_service()
    offset = request.args.get('offset', 0, type=int)
    
    return jsonify({
        'success': True,
        'data': service.get_logs(offset)
    })
