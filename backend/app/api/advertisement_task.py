"""API endpoints for managing advertisement tasks"""
from flask import Blueprint, request, jsonify, send_file
from app.extensions import db
from app.models.advertisement_task import AdvertisementTask, TaskStatus, TaskType
from app.models.task_rule_card import TaskRuleCard
from app.models.image import ImageDefaultLocation, Image
from app.models.workflow import Workflow
from sqlalchemy import func, desc
from datetime import datetime
import os
import requests
from app.utils.logger import logger

bp = Blueprint('advertisement_task', __name__, url_prefix='/api/advertisement-tasks')


@bp.route('/', methods=['GET'])
def get_tasks():
    """Get all advertisement tasks with optional filtering"""
    try:
        # Get query parameters for filtering
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Build query with eager loading of rule_cards
        from sqlalchemy.orm import joinedload
        query = AdvertisementTask.query.options(joinedload(AdvertisementTask.rule_cards))
        
        # Filter by status if provided
        if status:
            query = query.filter_by(status=status)
        
        # Order by task_type (normal first, then community), then by creation date (newest first)
        from sqlalchemy import case, or_
        task_type_order = case(
            (or_(AdvertisementTask.task_type == TaskType.normal, 
                 AdvertisementTask.task_type == TaskType.regular), 0),
            (AdvertisementTask.task_type == TaskType.community, 1),
            (AdvertisementTask.task_type == TaskType.community_special, 2),
            else_=3
        )
        query = query.order_by(task_type_order, desc(AdvertisementTask.created_at))
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        tasks = []
        for task in pagination.items:
            try:
                task_dict = task.to_dict(include_rule_cards=False)
                # Explicitly query rule cards for this task
                rule_cards = TaskRuleCard.query.filter_by(task_id=task.id).order_by(TaskRuleCard.display_order).all()
                task_dict['rule_cards'] = [rc.to_dict() for rc in rule_cards]
                task_dict['rule_cards_count'] = len(rule_cards)
                task_dict['available_rule_cards_count'] = sum(1 for rc in rule_cards if not rc.participated)
                tasks.append(task_dict)
            except Exception as task_error:
                logger.exception("Error serializing advertisement task", extra={
                    'task_id': task.id,
                    'task_status': task.status,
                    'task_data': task.task_title
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
        logger.exception("Failed to fetch advertisement tasks", extra={
            'status_filter': status,
            'page': page,
            'per_page': per_page
        })
        return jsonify({
            'success': False,
            'message': f'Failed to fetch tasks: {str(e)}'
        }), 500


@bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific advertisement task by ID"""
    try:
        task = AdvertisementTask.query.get(task_id)
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': task.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch task: {str(e)}'
        }), 500


@bp.route('/', methods=['POST'])
def create_task():
    """Create a new advertisement task"""
    try:
        data = request.get_json()
        
        # Check if task_id already exists
        existing_task = AdvertisementTask.query.filter_by(task_id=data.get('task_id')).first()
        if existing_task:
            return jsonify({
                'success': False,
                'message': 'Task with this task_id already exists'
            }), 400
        
        # Normalize status to lowercase
        status_value = data.get('status', TaskStatus.active.value)
        if isinstance(status_value, str):
            status_value = status_value.lower()
        
        # Create new task
        task = AdvertisementTask(
            task_id=data.get('task_id'),
            task_title=data.get('task_title'),
            card_title=data.get('card_title'),
            submission_rules=data.get('submission_rules'),
            tag_require=data.get('tag_require'),
            settlement_way=data.get('settlement_way'),
            hashtags=data.get('hashtags', []),
            image_path=data.get('image_path'),  # Relative path from default location
            image_url=data.get('image_url'),  # External URL fallback
            ads_pool_amount=data.get('ads_pool_amount', 0),
            status=status_value,
            task_type=data.get('task_type', 'normal'),  # Task type classification
            extra_data=data.get('extra_data'),
            deadline=data.get('deadline')
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task created successfully',
            'data': task.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to create task: {str(e)}'
        }), 500


@bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update an existing advertisement task"""
    try:
        task = AdvertisementTask.query.get(task_id)
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'task_title' in data:
            task.task_title = data['task_title']
        if 'card_title' in data:
            task.card_title = data['card_title']
        if 'submission_rules' in data:
            task.submission_rules = data['submission_rules']
        if 'tag_require' in data:
            task.tag_require = data['tag_require']
        if 'settlement_way' in data:
            task.settlement_way = data['settlement_way']
        if 'hashtags' in data:
            task.hashtags = data['hashtags']
        if 'image_path' in data:
            task.image_path = data['image_path']
        if 'image_url' in data:
            task.image_url = data['image_url']
        if 'ads_pool_amount' in data:
            task.ads_pool_amount = data['ads_pool_amount']
        if 'status' in data:
            # Normalize status to lowercase
            status_value = data['status']
            if isinstance(status_value, str):
                status_value = status_value.lower()
            task.status = status_value
        if 'task_type' in data:
            task.task_type = data['task_type']
        if 'extra_data' in data:
            task.extra_data = data['extra_data']
        if 'deadline' in data:
            task.deadline = data['deadline']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task updated successfully',
            'data': task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update task: {str(e)}'
        }), 500


@bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete an advertisement task"""
    try:
        task = AdvertisementTask.query.get(task_id)
        if not task:
            return jsonify({
                'success': False,
                'message': 'Task not found'
            }), 404
        
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Task deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete task: {str(e)}'
        }), 500


@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics about advertisement tasks"""
    try:
        from sqlalchemy import or_
        
        total = AdvertisementTask.query.count()
        # Active: status='active' AND not participated
        active = AdvertisementTask.query.filter_by(status=TaskStatus.active.value, participated=False).count()
        # Completed: status='completed' OR participated=True
        completed = AdvertisementTask.query.filter(
            or_(
                AdvertisementTask.status == TaskStatus.completed.value,
                AdvertisementTask.participated == True
            )
        ).count()
        expired = AdvertisementTask.query.filter_by(status=TaskStatus.expired.value).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'active': active,
                'completed': completed,
                'expired': expired
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch stats: {str(e)}'
        }), 500


@bp.route('/image/<int:task_id>', methods=['GET'])
def serve_image(task_id):
    """Serve image file for an advertisement task from the configured default location"""
    try:
        # Get the task
        task = AdvertisementTask.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        if not task.image_path:
            return jsonify({'success': False, 'message': 'No image for this task'}), 404
        
        # Get the default location for advertising images
        default_location = ImageDefaultLocation.query.filter_by(
            image_type='advertising_campaign'
        ).first()
        
        if not default_location:
            return jsonify({
                'success': False,
                'message': 'Default image location not configured for advertising_campaign'
            }), 500
        
        # Construct full path
        full_path = os.path.join(default_location.directory, task.image_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'message': f'Image file not found: {task.image_path}'
            }), 404
        
        # Serve the file
        return send_file(full_path, mimetype='image/jpeg')
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to serve image: {str(e)}'
        }), 500


@bp.route('/participate', methods=['POST'])
def participate_tasks():
    """
    Participate in advertisement tasks with text prompts
    
    Request body:
        {
            "task_ids": [1, 2, 3],
            "include_rule_image": false,  // Optional, default false
            "additional_params": {}        // Optional parameters
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        task_ids = data.get('task_ids', [])
        include_rule_image = data.get('include_rule_image', False)
        additional_params = data.get('additional_params', {})
        
        if not task_ids:
            return jsonify({
                'success': False,
                'message': 'task_ids is required'
            }), 400
        
        # Process each task
        results = []
        for task_id in task_ids:
            task = AdvertisementTask.query.get(task_id)
            if not task:
                results.append({
                    'task_id': task_id,
                    'success': False,
                    'message': 'Task not found'
                })
                continue
            
            try:
                # Build text prompt from task data
                prompt = build_task_prompt(task)
                
                # Prepare workflow parameters
                workflow_params = {
                    'text_prompt': prompt,
                    **additional_params
                }
                
                # If include_rule_image is enabled, try to get the task's image
                if include_rule_image and task.image_path:
                    default_location = ImageDefaultLocation.query.filter_by(
                        image_type='advertising_campaign'
                    ).first()
                    
                    if default_location:
                        full_image_path = os.path.join(default_location.directory, task.image_path)
                        if os.path.exists(full_image_path):
                            workflow_params['rule_image_path'] = full_image_path
                
                # Execute workflow (this would call your ComfyUI or workflow execution service)
                # For now, we'll just mark as participated
                # TODO: Implement actual workflow execution
                
                # Update participation status
                task.participated = True
                task.participation_count = (task.participation_count or 0) + 1
                task.last_participated_at = datetime.utcnow()
                db.session.add(task)
                
                results.append({
                    'task_id': task_id,
                    'task_title': task.task_title,
                    'success': True,
                    'message': 'Participation recorded',
                    'prompt_used': prompt,
                    'included_rule_image': include_rule_image and task.image_path is not None
                })
                
            except Exception as e:
                results.append({
                    'task_id': task_id,
                    'success': False,
                    'message': f'Error: {str(e)}'
                })
        
        db.session.commit()
        
        success_count = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'data': {
                'total': len(task_ids),
                'succeeded': success_count,
                'failed': len(task_ids) - success_count,
                'results': results
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to participate in tasks: {str(e)}'
        }), 500


def build_task_prompt(task: AdvertisementTask) -> str:
    """
    Build a text prompt from advertisement task data
    
    Args:
        task: AdvertisementTask instance
        
    Returns:
        Formatted prompt string
    """
    prompt_parts = []
    
    # Add title
    if task.task_title:
        prompt_parts.append(f"任务: {task.task_title}")
    
    # Add hashtags
    if task.hashtags:
        hashtags_str = ' '.join(task.hashtags)
        prompt_parts.append(f"话题标签: {hashtags_str}")
    
    # Add tag requirements
    if task.tag_require:
        prompt_parts.append(f"话题要求: {task.tag_require}")
    
    # Add submission rules
    if task.submission_rules:
        prompt_parts.append(f"投稿规则: {task.submission_rules}")
    
    return '\n\n'.join(prompt_parts)


@bp.route('/participation-status', methods=['GET'])
def get_participation_status():
    """Get participation statistics"""
    try:
        total = AdvertisementTask.query.count()
        participated = AdvertisementTask.query.filter_by(participated=True).count()
        not_participated = total - participated
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'participated': participated,
                'not_participated': not_participated,
                'participation_rate': f"{(participated / total * 100):.1f}%" if total > 0 else "0%"
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get participation status: {str(e)}'
        }), 500


# ==================== Rule Card Management Endpoints ====================

@bp.route('/<int:task_id>/rule-cards', methods=['GET'])
def get_task_rule_cards(task_id):
    """Get all rule cards for a specific task"""
    try:
        task = AdvertisementTask.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        # Get rule cards sorted by display_order
        rule_cards = TaskRuleCard.query.filter_by(task_id=task_id).order_by(TaskRuleCard.display_order).all()
        
        return jsonify({
            'success': True,
            'data': {
                'task_id': task_id,
                'task_title': task.task_title,
                'rule_cards': [rc.to_dict() for rc in rule_cards],
                'total_count': len(rule_cards),
                'available_count': sum(1 for rc in rule_cards if not rc.participated)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get rule cards: {str(e)}'
        }), 500


@bp.route('/<int:task_id>/rule-cards', methods=['POST'])
def create_rule_card(task_id):
    """Create a new rule card for a task"""
    try:
        task = AdvertisementTask.query.get(task_id)
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        data = request.get_json()
        
        # Get the max display_order for this task
        max_order = db.session.query(func.max(TaskRuleCard.display_order)).filter_by(task_id=task_id).scalar() or 0
        
        rule_card = TaskRuleCard(
            task_id=task_id,
            rule_name=data.get('rule_name'),
            rule_description=data.get('rule_description'),
            image_path=data.get('image_path'),
            image_url=data.get('image_url'),
            display_order=data.get('display_order', max_order + 1)
        )
        
        db.session.add(rule_card)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': rule_card.to_dict(),
            'message': 'Rule card created successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to create rule card: {str(e)}'
        }), 500


@bp.route('/rule-card/<int:rule_card_id>', methods=['GET'])
def get_rule_card(rule_card_id):
    """Get a specific rule card by ID"""
    try:
        rule_card = TaskRuleCard.query.get(rule_card_id)
        if not rule_card:
            return jsonify({'success': False, 'message': 'Rule card not found'}), 404
        
        return jsonify({
            'success': True,
            'data': rule_card.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get rule card: {str(e)}'
        }), 500


@bp.route('/rule-card/<int:rule_card_id>', methods=['PUT'])
def update_rule_card(rule_card_id):
    """Update a rule card"""
    try:
        rule_card = TaskRuleCard.query.get(rule_card_id)
        if not rule_card:
            return jsonify({'success': False, 'message': 'Rule card not found'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'rule_name' in data:
            rule_card.rule_name = data['rule_name']
        if 'rule_description' in data:
            rule_card.rule_description = data['rule_description']
        if 'image_path' in data:
            rule_card.image_path = data['image_path']
        if 'image_url' in data:
            rule_card.image_url = data['image_url']
        if 'display_order' in data:
            rule_card.display_order = data['display_order']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': rule_card.to_dict(),
            'message': 'Rule card updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update rule card: {str(e)}'
        }), 500


@bp.route('/rule-card/<int:rule_card_id>', methods=['DELETE'])
def delete_rule_card(rule_card_id):
    """Delete a rule card"""
    try:
        rule_card = TaskRuleCard.query.get(rule_card_id)
        if not rule_card:
            return jsonify({'success': False, 'message': 'Rule card not found'}), 404
        
        db.session.delete(rule_card)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rule card deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete rule card: {str(e)}'
        }), 500


@bp.route('/rule-card/<int:rule_card_id>/image', methods=['GET'])
def serve_rule_card_image(rule_card_id):
    """Serve image file for a rule card"""
    try:
        rule_card = TaskRuleCard.query.get(rule_card_id)
        if not rule_card:
            return jsonify({'success': False, 'message': 'Rule card not found'}), 404
        
        if not rule_card.image_path:
            return jsonify({'success': False, 'message': 'No image for this rule card'}), 404
        
        # Try to get the default location for rule_card_screenshot first (from crawler)
        # Fall back to advertising_rule for backward compatibility
        default_location = ImageDefaultLocation.query.filter_by(
            image_type='rule_card_screenshot'
        ).first()
        
        if not default_location:
            # Fallback to advertising_rule for backward compatibility
            default_location = ImageDefaultLocation.query.filter_by(
                image_type='advertising_rule'
            ).first()
        
        if not default_location:
            return jsonify({
                'success': False,
                'message': 'Default image location not configured. Please configure in Image Management > Default Directory'
            }), 500
        
        # Check if image_path is absolute or relative
        if os.path.isabs(rule_card.image_path):
            # Absolute path - use directly
            full_path = rule_card.image_path
        else:
            # Relative path - combine with default location
            full_path = os.path.join(default_location.directory, rule_card.image_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'message': f'Image file not found: {full_path}'
            }), 404
        
        # Detect mimetype from file extension
        mimetype = 'image/jpeg'
        if full_path.lower().endswith('.png'):
            mimetype = 'image/png'
        elif full_path.lower().endswith('.gif'):
            mimetype = 'image/gif'
        elif full_path.lower().endswith('.webp'):
            mimetype = 'image/webp'
        
        # Serve the file
        return send_file(full_path, mimetype=mimetype)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to serve image: {str(e)}'
        }), 500


@bp.route('/rule-card/<int:rule_card_id>/participated', methods=['PATCH'])
def mark_rule_card_participated(rule_card_id):
    """Mark a rule card as participated"""
    try:
        rule_card = TaskRuleCard.query.get(rule_card_id)
        if not rule_card:
            return jsonify({'success': False, 'message': 'Rule card not found'}), 404
        
        rule_card.participated = True
        rule_card.participation_count = (rule_card.participation_count or 0) + 1
        rule_card.last_participated_at = datetime.utcnow()
        
        # Also update parent task participation tracking
        task = rule_card.task
        task.participation_count = (task.participation_count or 0) + 1
        task.last_participated_at = datetime.utcnow()
        
        # Mark task as participated if all rule cards are participated
        available_cards = [rc for rc in task.rule_cards if not rc.participated and rc.id != rule_card_id]
        if not available_cards:
            task.participated = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': rule_card.to_dict(),
            'message': 'Rule card marked as participated'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to mark rule card as participated: {str(e)}'
        }), 500


@bp.route('/rule-card/<int:rule_card_id>/status', methods=['PUT'])
def update_rule_card_status(rule_card_id):
    """Update rule card participated status (toggle on/off)"""
    try:
        data = request.get_json() or {}
        participated = data.get('participated', False)
        
        rule_card = TaskRuleCard.query.get(rule_card_id)
        if not rule_card:
            return jsonify({'success': False, 'message': 'Rule card not found'}), 404
        
        rule_card.participated = participated
        
        if participated:
            # If marking as participated, increment count and set timestamp
            rule_card.participation_count = (rule_card.participation_count or 0) + 1
            rule_card.last_participated_at = datetime.utcnow()
        
        # Update parent task participated status based on all rule cards
        task = rule_card.task
        all_cards_participated = all(rc.participated for rc in task.rule_cards)
        task.participated = all_cards_participated
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': rule_card.to_dict(),
            'message': f'Rule card status updated to {"participated" if participated else "not participated"}'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update rule card status: {str(e)}'
        }), 500


@bp.route('/sync', methods=['POST'])
def sync_tasks():
    """Sync tasks from XHS API response - upserts tasks to database"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Support both direct taskList and wrapped response format
        task_list = data.get('taskList') or data.get('data', {}).get('taskList') or []
        
        if not task_list:
            return jsonify({'success': False, 'message': 'No tasks in data'}), 400
        
        from app.models.advertisement_task import TaskType
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for task_data in task_list:
            task_no = task_data.get('taskNo')
            if not task_no:
                skipped_count += 1
                continue
            
            # Check if task already exists
            existing_task = AdvertisementTask.query.filter_by(task_id=task_no).first()
            
            # Parse task type from category or other fields
            # NATIONAL = normal tasks, others might be community
            category = task_data.get('category', 'NATIONAL')
            task_type = TaskType.normal if category == 'NATIONAL' else TaskType.community
            
            # Check title for community indicators
            title = task_data.get('title', '')
            if '社群' in title or 'SP委托' in title or '社群专属' in title:
                task_type = TaskType.community
            
            if existing_task:
                # Update existing task
                existing_task.task_title = title
                existing_task.ads_pool_amount = float(task_data.get('cashMaxBudget', 0) or 0)
                existing_task.task_type = task_type
                existing_task.image_url = task_data.get('thumbnail')
                updated_count += 1
            else:
                # Create new task
                new_task = AdvertisementTask(
                    task_id=task_no,
                    task_title=title,
                    card_title=title,
                    ads_pool_amount=float(task_data.get('cashMaxBudget', 0) or 0),
                    task_type=task_type,
                    image_url=task_data.get('thumbnail'),
                    status=TaskStatus.active
                )
                db.session.add(new_task)
                created_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Synced tasks: {created_count} created, {updated_count} updated, {skipped_count} skipped',
            'data': {
                'created': created_count,
                'updated': updated_count,
                'skipped': skipped_count,
                'total': len(task_list)
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to sync tasks")
        return jsonify({
            'success': False,
            'message': f'Failed to sync tasks: {str(e)}'
        }), 500
