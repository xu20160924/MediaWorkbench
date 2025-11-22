"""API endpoints for system configuration management"""
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.system_config import SystemConfig, ConfigCategory, DEFAULT_CONFIGS
from sqlalchemy.exc import IntegrityError
import json

bp = Blueprint('system_config', __name__, url_prefix='/api/system-config')


@bp.route('/', methods=['GET'])
def list_configs():
    """
    Get all system configurations
    
    Query parameters:
        category: Filter by category (optional)
        visible_only: Only return visible configs (default: false)
    """
    try:
        category = request.args.get('category')
        visible_only = request.args.get('visible_only', 'false').lower() == 'true'
        
        query = SystemConfig.query
        
        if category:
            query = query.filter_by(category=category)
        
        if visible_only:
            query = query.filter_by(is_visible=True)
        
        configs = query.order_by(SystemConfig.category, SystemConfig.key).all()
        
        return jsonify({
            'success': True,
            'data': [config.to_dict() for config in configs],
            'count': len(configs)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list configurations: {str(e)}'
        }), 500


@bp.route('/categories', methods=['GET'])
def list_categories():
    """Get all available configuration categories"""
    try:
        categories = db.session.query(SystemConfig.category).distinct().all()
        
        # Count configs per category
        result = []
        for (category,) in categories:
            count = SystemConfig.query.filter_by(category=category).count()
            result.append({
                'category': category,
                'count': count
            })
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to list categories: {str(e)}'
        }), 500


@bp.route('/category/<category>', methods=['GET'])
def get_category_configs(category):
    """Get all configurations in a specific category"""
    try:
        configs = SystemConfig.query.filter_by(category=category).all()
        
        if not configs:
            return jsonify({
                'success': False,
                'message': f'No configurations found for category: {category}'
            }), 404
        
        # Return as both list and dict formats
        return jsonify({
            'success': True,
            'data': {
                'category': category,
                'configs': [config.to_dict() for config in configs],
                'values': {config.key: config.get_parsed_value() for config in configs}
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get category configurations: {str(e)}'
        }), 500


@bp.route('/<int:config_id>', methods=['GET'])
def get_config(config_id):
    """Get a specific configuration by ID"""
    try:
        config = SystemConfig.query.get(config_id)
        
        if not config:
            return jsonify({
                'success': False,
                'message': 'Configuration not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get configuration: {str(e)}'
        }), 500


@bp.route('/get', methods=['GET'])
def get_config_by_key():
    """
    Get a configuration value by category and key
    
    Query parameters:
        category: Configuration category (required)
        key: Configuration key (required)
    """
    try:
        category = request.args.get('category')
        key = request.args.get('key')
        
        if not category or not key:
            return jsonify({
                'success': False,
                'message': 'Both category and key are required'
            }), 400
        
        config = SystemConfig.query.filter_by(category=category, key=key).first()
        
        if not config:
            return jsonify({
                'success': False,
                'message': f'Configuration not found: {category}.{key}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get configuration: {str(e)}'
        }), 500


@bp.route('/', methods=['POST'])
def create_or_update_config():
    """
    Create or update a configuration
    
    Request body:
        {
            "category": "image_locations",
            "key": "advertising_campaign_directory",
            "value": "/path/to/directory",
            "data_type": "string",
            "description": "Description",
            "is_editable": true,
            "is_visible": true,
            "validation_rules": {"min": 0, "max": 100}
        }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        # Validate required fields
        if 'category' not in data or 'key' not in data or 'value' not in data:
            return jsonify({
                'success': False,
                'message': 'category, key, and value are required'
            }), 400
        
        # Check if config exists
        config = SystemConfig.query.filter_by(
            category=data['category'],
            key=data['key']
        ).first()
        
        user = request.headers.get('X-User-Id', 'system')  # Get user from header or default to system
        
        if config:
            # Update existing
            if not config.is_editable:
                return jsonify({
                    'success': False,
                    'message': 'This configuration is not editable'
                }), 403
            
            config.set_value(data['value'])
            
            if 'data_type' in data:
                config.data_type = data['data_type']
            if 'description' in data:
                config.description = data['description']
            if 'is_editable' in data:
                config.is_editable = data['is_editable']
            if 'is_visible' in data:
                config.is_visible = data['is_visible']
            if 'validation_rules' in data:
                config.validation_rules = json.dumps(data['validation_rules'])
            
            config.updated_by = user
            
        else:
            # Create new
            config = SystemConfig(
                category=data['category'],
                key=data['key'],
                data_type=data.get('data_type', 'string'),
                description=data.get('description'),
                is_editable=data.get('is_editable', True),
                is_visible=data.get('is_visible', True),
                created_by=user,
                updated_by=user
            )
            config.set_value(data['value'])
            
            if 'validation_rules' in data:
                config.validation_rules = json.dumps(data['validation_rules'])
            
            db.session.add(config)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': config.to_dict(),
            'message': 'Configuration saved successfully'
        })
        
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Configuration already exists: {str(e)}'
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to save configuration: {str(e)}'
        }), 500


@bp.route('/<int:config_id>', methods=['PUT'])
def update_config(config_id):
    """Update a configuration by ID"""
    try:
        config = SystemConfig.query.get(config_id)
        
        if not config:
            return jsonify({
                'success': False,
                'message': 'Configuration not found'
            }), 404
        
        if not config.is_editable:
            return jsonify({
                'success': False,
                'message': 'This configuration is not editable'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request body is required'
            }), 400
        
        user = request.headers.get('X-User-Id', 'system')
        
        if 'value' in data:
            config.set_value(data['value'])
        if 'data_type' in data:
            config.data_type = data['data_type']
        if 'description' in data:
            config.description = data['description']
        if 'is_editable' in data:
            config.is_editable = data['is_editable']
        if 'is_visible' in data:
            config.is_visible = data['is_visible']
        if 'validation_rules' in data:
            config.validation_rules = json.dumps(data['validation_rules'])
        
        config.updated_by = user
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': config.to_dict(),
            'message': 'Configuration updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to update configuration: {str(e)}'
        }), 500


@bp.route('/<int:config_id>', methods=['DELETE'])
def delete_config(config_id):
    """Delete a configuration"""
    try:
        config = SystemConfig.query.get(config_id)
        
        if not config:
            return jsonify({
                'success': False,
                'message': 'Configuration not found'
            }), 404
        
        if not config.is_editable:
            return jsonify({
                'success': False,
                'message': 'This configuration cannot be deleted'
            }), 403
        
        db.session.delete(config)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Configuration deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete configuration: {str(e)}'
        }), 500


@bp.route('/init-defaults', methods=['POST'])
def init_default_configs():
    """
    Initialize default configurations
    This will create all default configs if they don't exist
    """
    try:
        created_count = 0
        skipped_count = 0
        
        for default_config in DEFAULT_CONFIGS:
            existing = SystemConfig.query.filter_by(
                category=default_config['category'],
                key=default_config['key']
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            config = SystemConfig(
                category=default_config['category'],
                key=default_config['key'],
                data_type=default_config.get('data_type', 'string'),
                description=default_config.get('description'),
                is_editable=default_config.get('is_editable', True),
                is_visible=default_config.get('is_visible', True),
                created_by='system',
                updated_by='system'
            )
            config.set_value(default_config['value'])
            
            if 'validation_rules' in default_config:
                config.validation_rules = default_config['validation_rules']
            
            db.session.add(config)
            created_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Initialized default configurations',
            'created': created_count,
            'skipped': skipped_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to initialize default configurations: {str(e)}'
        }), 500


@bp.route('/batch', methods=['POST'])
def batch_update_configs():
    """
    Batch update multiple configurations
    
    Request body:
        {
            "configs": [
                {"category": "...", "key": "...", "value": "..."},
                {"category": "...", "key": "...", "value": "..."}
            ]
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'configs' not in data:
            return jsonify({
                'success': False,
                'message': 'configs array is required'
            }), 400
        
        user = request.headers.get('X-User-Id', 'system')
        updated_count = 0
        errors = []
        
        for config_data in data['configs']:
            if 'category' not in config_data or 'key' not in config_data or 'value' not in config_data:
                errors.append(f'Missing required fields in: {config_data}')
                continue
            
            try:
                SystemConfig.set(
                    category=config_data['category'],
                    key=config_data['key'],
                    value=config_data['value'],
                    data_type=config_data.get('data_type', 'string'),
                    description=config_data.get('description'),
                    user=user
                )
                updated_count += 1
            except Exception as e:
                errors.append(f'Failed to update {config_data["category"]}.{config_data["key"]}: {str(e)}')
        
        return jsonify({
            'success': True,
            'message': f'Batch update completed',
            'updated': updated_count,
            'errors': errors
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to batch update configurations: {str(e)}'
        }), 500
