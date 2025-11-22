"""API endpoints for managing advertisement tasks"""
from flask import Blueprint, request, jsonify, send_file
from app.extensions import db
from app.models.advertisement_task import AdvertisementTask, TaskStatus
from app.models.task_rule_card import TaskRuleCard
from app.models.image import ImageDefaultLocation, Image
from app.models.workflow import Workflow
from sqlalchemy import func, desc
from datetime import datetime
import os
import requests

bp = Blueprint('advertisement_task', __name__, url_prefix='/api/advertisement-tasks')


@bp.route('/', methods=['GET'])
def get_tasks():
    """Get all advertisement tasks with optional filtering"""
    try:
        # Get query parameters for filtering
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Build query
        query = AdvertisementTask.query
        
        # Filter by status if provided
        if status:
            query = query.filter_by(status=status)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(AdvertisementTask.created_at))
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': {
                'tasks': [task.to_dict() for task in pagination.items],
                'total': pagination.total,
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages
            }
        })
    except Exception as e:
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
            status=data.get('status', TaskStatus.active.value),
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
            task.status = data['status']
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
        
        # Get the default location for advertising_rule images
        default_location = ImageDefaultLocation.query.filter_by(
            image_type='advertising_rule'
        ).first()
        
        if not default_location:
            return jsonify({
                'success': False,
                'message': 'Default image location not configured for advertising_rule'
            }), 500
        
        # Construct full path
        full_path = os.path.join(default_location.directory, rule_card.image_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            return jsonify({
                'success': False,
                'message': f'Image file not found: {rule_card.image_path}'
            }), 404
        
        # Serve the file
        return send_file(full_path, mimetype='image/jpeg')
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
