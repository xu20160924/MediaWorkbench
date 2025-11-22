"""API endpoints for managing default image storage locations"""
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.image import ImageDefaultLocation

bp = Blueprint('image_locations', __name__, url_prefix='/api/image-locations')


@bp.route('/', methods=['GET'])
def get_locations():
    """Get all default image storage locations"""
    try:
        locations = ImageDefaultLocation.query.all()
        return jsonify({
            'success': True,
            'data': [loc.to_dict() for loc in locations]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch locations: {str(e)}'
        }), 500


@bp.route('/<image_type>', methods=['GET'])
def get_location(image_type):
    """Get default storage location for a specific image type"""
    try:
        location = ImageDefaultLocation.query.filter_by(image_type=image_type).first()
        if not location:
            return jsonify({
                'success': False,
                'message': f'No default location configured for {image_type}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': location.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch location: {str(e)}'
        }), 500


@bp.route('/', methods=['POST'])
def create_or_update_location():
    """Create or update default storage location for an image type"""
    try:
        data = request.get_json()
        
        if not data.get('image_type') or not data.get('directory'):
            return jsonify({
                'success': False,
                'message': 'image_type and directory are required'
            }), 400
        
        # Check if location already exists
        location = ImageDefaultLocation.query.filter_by(
            image_type=data['image_type']
        ).first()
        
        if location:
            # Update existing
            location.directory = data['directory']
        else:
            # Create new
            location = ImageDefaultLocation(
                image_type=data['image_type'],
                directory=data['directory']
            )
            db.session.add(location)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': location.to_dict(),
            'message': 'Location saved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to save location: {str(e)}'
        }), 500


@bp.route('/<int:location_id>', methods=['DELETE'])
def delete_location(location_id):
    """Delete a default storage location"""
    try:
        location = ImageDefaultLocation.query.get(location_id)
        if not location:
            return jsonify({
                'success': False,
                'message': 'Location not found'
            }), 404
        
        db.session.delete(location)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Location deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Failed to delete location: {str(e)}'
        }), 500
