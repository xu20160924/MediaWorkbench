"""API endpoints for buyer tasks"""
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.buyer_task import BuyerTask, BuyerTaskStatus
from sqlalchemy import desc
from app.utils.logger import logger
import requests
import re
from urllib.parse import urlparse, parse_qs
from spider.xhs_product_crawler import resolve_xhs_link, fetch_product_details_from_web, extract_buyer_task_params

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


@bp.route('/<int:task_id>', methods=['DELETE'])
def delete_buyer_task(task_id):
    """Delete a specific buyer task"""
    try:
        task = BuyerTask.query.get_or_404(task_id)
        
        # Store task info for logging
        task_info = {
            'id': task.id,
            'item_id': task.item_id,
            'title': task.title
        }
        
        # Delete the task
        db.session.delete(task)
        db.session.commit()
        
        logger.info(f"Deleted buyer task: {task_info}")
        
        return jsonify({
            'success': True,
            'message': f'Task "{task_info["title"]}" deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to delete buyer task", extra={'task_id': task_id})
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/crawl-from-url', methods=['POST'])
def crawl_buyer_task_from_url():
    """Crawl a single buyer task from a given URL"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        url = data['url']
        session_token = data.get('session_token', '')
        x_signature = data.get('x_signature', '')
        
        if not session_token:
            return jsonify({'success': False, 'error': 'session_token is required'}), 400
        
        logger.info(f"Starting single buyer task crawl from URL: {url}")
        
        # Step 1: Resolve the xhslink.com URL to get the actual task URL
        actual_url = resolve_xhs_link(url)
        if not actual_url:
            return jsonify({'success': False, 'error': 'Failed to resolve XHS link'}), 400
        
        logger.info(f"Resolved URL: {actual_url}")
        
        # Step 2: Extract task parameters from the resolved URL
        task_params = extract_buyer_task_params(actual_url)
        logger.info(f"Extracted parameters: {task_params}")
        
        if not task_params:
            return jsonify({'success': False, 'error': 'Failed to extract task parameters from URL'}), 400
        
        sku_id = task_params.get('sku_id')
        plan_id = task_params.get('plan_id')
        plan_type = task_params.get('plan_type', '')
        
        if not sku_id or not plan_id:
            return jsonify({
                'success': False, 
                'error': f'Missing required task parameters - sku_id: {sku_id}, plan_id: {plan_id}. Resolved URL: {actual_url}'
            }), 400
        
        
        # Step 3: Handle different URL types based on URL structure, not parameters
        url_type = task_params.get('url_type', '')
        
        # Check if this is a product URL based on URL structure
        if '/goods-detail/' in actual_url or plan_type == 'product':
            # This is a product URL - use web scraping approach
            logger.info(f"Detected product URL, using web scraping approach for goods ID: {sku_id}")
            try:
                product_data = fetch_product_details_from_web(actual_url, session_token)
                if not product_data:
                    return jsonify({'success': False, 'error': 'Failed to fetch product details from web page'}), 400
                
                # Convert product data to buyer task format for database storage
                detail_data = {
                    'distribution_plan_info': {
                        'goods_item_info': {
                            'title': product_data.get('title', f'Product {sku_id}'),
                            'price': product_data.get('price', 0),
                            'deal_price': product_data.get('deal_price', 0),
                            'image': product_data.get('main_image', ''),
                            'small_images': product_data.get('images', []),
                            'item_url': actual_url,
                            'description': product_data.get('variant_text', ''),
                            'sales_text': product_data.get('sales_text', ''),
                            'seller_name': product_data.get('seller_name', ''),
                            'seller_logo': product_data.get('seller_logo', ''),
                            'seller_grade': product_data.get('seller_grade', ''),
                            'seller_score': product_data.get('seller_score', ''),
                            'seller_id': product_data.get('seller_id', ''),
                            'services': product_data.get('services', []),
                            'shipping_location': product_data.get('shipping_location', ''),
                            'shipping_fee': product_data.get('shipping_fee', ''),
                            'shipping_time': product_data.get('shipping_time', ''),
                            'sku_id': product_data.get('sku_id', sku_id)
                        }
                    }
                }
            except Exception as e:
                return jsonify({'success': False, 'error': f'Failed to fetch product details: {str(e)}'}), 400
        else:
            # This is a buyer task URL - use existing API approach
            from spider.xhs_crawler import fetch_buyer_task_detail
            
            try:
                detail_data = fetch_buyer_task_detail(
                    session_token=session_token,
                    x_signature=x_signature or "",
                    sku_id=sku_id,
                    plan_id=plan_id,
                    plan_type=plan_type
                )
            except Exception as e:
                error_msg = str(e)
                if "400 Client Error" in error_msg and "buyer/item_detail" in error_msg:
                    return jsonify({
                        'success': False, 
                        'error': f'The buyer task API rejected this request. This may be because the URL is not a valid buyer collaboration task, or the task parameters are incorrect. Extracted parameters: sku_id={sku_id}, plan_id={plan_id}, plan_type={plan_type}'
                    }), 400
                else:
                    return jsonify({'success': False, 'error': f'Failed to fetch task details: {error_msg}'}), 400
        
        if not detail_data:
            return jsonify({'success': False, 'error': 'Failed to fetch task details - empty response'}), 400
        
        # Step 4: Extract information and save to database
        dist_plan_info = detail_data.get('distribution_plan_info', {})
        goods_info = dist_plan_info.get('goods_item_info', {})
        
        logger.info(f"Distribution plan info keys: {list(dist_plan_info.keys())}")
        logger.info(f"Goods info keys: {list(goods_info.keys())}")
        logger.info(f"Goods info content: {goods_info}")
        
        # Extract basic info
        title = goods_info.get('title', f'Buyer Task {sku_id}')
        item_price = goods_info.get('price')
        deal_price = goods_info.get('deal_price')
        main_image_url = goods_info.get('image', '')
        small_images = goods_info.get('small_images', [])
        item_url = goods_info.get('item_url', '')
        seller_name = goods_info.get('seller_name', '')
        seller_score_raw = goods_info.get('seller_score')
        seller_score = None
        if seller_score_raw not in (None, ''):
            try:
                seller_score = float(seller_score_raw)
            except (TypeError, ValueError):
                seller_score = None
        seller_logo = goods_info.get('seller_logo', '')
        
        logger.info(f"Extracted data - title: '{title}', price: {item_price}, deal_price: {deal_price}, images: {len(small_images)}, seller: '{seller_name}'")
        
        # Use first small image as main image if available
        if small_images and not main_image_url:
            main_image_url = small_images[0]
        
        # Create mock list data for consistency with existing structure
        mock_list_data = {
            'itemId': sku_id,
            'title': title,
            'itemImage': main_image_url,
            'jumpUrl': actual_url,
            'itemPrice': item_price,
            'dealPrice': deal_price,
            'sellerInfo': {
                'sellerName': seller_name,
                'sellerScore': seller_score,
                'sellerLogo': seller_logo
            }
        }
        
        # Check if task already exists
        existing_task = BuyerTask.query.filter_by(item_id=sku_id).first()
        
        if existing_task:
            logger.info(f"Updating existing buyer task: {sku_id}")
            existing_task.title = title
            existing_task.sku_id = sku_id
            existing_task.plan_id = plan_id
            existing_task.plan_type = plan_type
            existing_task.item_price = str(item_price) if item_price else None
            existing_task.item_income = str(deal_price) if deal_price else None
            existing_task.main_image_url = main_image_url
            existing_task.small_images = small_images
            existing_task.seller_name = seller_name
            existing_task.seller_score = seller_score
            existing_task.seller_image = seller_logo
            existing_task.jump_url = actual_url
            existing_task.item_url = item_url
            existing_task.list_data = mock_list_data
            existing_task.detail_data = detail_data
            existing_task.status = BuyerTaskStatus.active.value
            task_obj = existing_task
        else:
            logger.info(f"Creating new buyer task: {sku_id}")
            new_task = BuyerTask(
                item_id=sku_id,
                sku_id=sku_id,
                plan_id=plan_id,
                plan_type=plan_type,
                title=title,
                item_price=str(item_price) if item_price else None,
                item_income=str(deal_price) if deal_price else None,
                main_image_url=main_image_url,
                small_images=small_images,
                seller_name=seller_name,
                seller_score=seller_score,
                seller_image=seller_logo,
                jump_url=actual_url,
                item_url=item_url,
                status=BuyerTaskStatus.active.value,
                list_data=mock_list_data,
                detail_data=detail_data
            )
            db.session.add(new_task)
            task_obj = new_task
        
        db.session.commit()
        
        logger.info(f"Successfully crawled and saved buyer task: {sku_id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully crawled buyer task: {title}',
            'data': {
                'id': task_obj.id,
                'item_id': task_obj.item_id,
                'title': task_obj.title,
                'main_image_url': task_obj.main_image_url,
                'small_images': task_obj.small_images,
                'item_price': task_obj.item_price,
                'status': task_obj.status
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to crawl buyer task from URL")
        return jsonify({'success': False, 'error': str(e)}), 500


