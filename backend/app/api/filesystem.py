"""
Filesystem API for server-side directory browsing
"""
from flask import Blueprint, request, jsonify
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('filesystem', __name__)


def is_safe_path(path: str) -> bool:
    """
    Check if path is safe to access.
    Prevents directory traversal attacks.
    """
    try:
        # Resolve to absolute path
        abs_path = os.path.abspath(path)
        
        # Don't allow access to system directories
        forbidden_prefixes = []
        
        # For macOS/Linux
        if os.name != 'nt':
            forbidden_prefixes = [
                '/System',
                '/private/var',
                '/Library/System',
            ]
        
        # Check if path starts with forbidden prefix
        for prefix in forbidden_prefixes:
            if abs_path.startswith(prefix):
                return False
        
        return True
    except Exception:
        return False


@bp.route('/api/filesystem/list-directories', methods=['POST'])
def list_directories():
    """
    List directories at a given path.
    
    Request:
        {
            "path": "/path/to/directory"  # Optional, defaults to user home
        }
    
    Response:
        {
            "success": true,
            "data": {
                "current_path": "/path/to/directory",
                "parent_path": "/path/to",
                "directories": [
                    {"name": "folder1", "path": "/path/to/directory/folder1"},
                    {"name": "folder2", "path": "/path/to/directory/folder2"}
                ]
            }
        }
    """
    try:
        data = request.get_json() or {}
        requested_path = data.get('path')
        
        # Default to user home directory
        if not requested_path:
            requested_path = str(Path.home())
        
        # Resolve to absolute path
        current_path = os.path.abspath(requested_path)
        
        # Security check
        if not is_safe_path(current_path):
            return jsonify({
                'success': False,
                'message': 'Access to this directory is not allowed'
            }), 403
        
        # Check if path exists and is a directory
        if not os.path.exists(current_path):
            return jsonify({
                'success': False,
                'message': 'Directory does not exist'
            }), 404
        
        if not os.path.isdir(current_path):
            return jsonify({
                'success': False,
                'message': 'Path is not a directory'
            }), 400
        
        # List directories (not files)
        directories = []
        try:
            for item in sorted(os.listdir(current_path)):
                item_path = os.path.join(current_path, item)
                
                # Only include directories, skip hidden files
                if os.path.isdir(item_path) and not item.startswith('.'):
                    directories.append({
                        'name': item,
                        'path': item_path
                    })
        except PermissionError:
            return jsonify({
                'success': False,
                'message': 'Permission denied to read this directory'
            }), 403
        
        # Get parent directory
        parent_path = os.path.dirname(current_path)
        
        # For root directories, parent is None
        if parent_path == current_path:
            parent_path = None
        
        return jsonify({
            'success': True,
            'data': {
                'current_path': current_path,
                'parent_path': parent_path,
                'directories': directories
            }
        })
        
    except Exception as e:
        logger.error(f'Error listing directories: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@bp.route('/api/filesystem/common-directories', methods=['GET'])
def get_common_directories():
    """
    Get list of common starting directories.
    
    Response:
        {
            "success": true,
            "data": {
                "directories": [
                    {"name": "Home", "path": "/Users/username"},
                    {"name": "Desktop", "path": "/Users/username/Desktop"},
                    ...
                ]
            }
        }
    """
    try:
        home = Path.home()
        common_dirs = [
            {'name': 'Home', 'path': str(home)},
        ]
        
        # Add common subdirectories if they exist
        for subdir in ['Desktop', 'Documents', 'Downloads', 'Pictures']:
            path = home / subdir
            if path.exists() and path.is_dir():
                common_dirs.append({
                    'name': subdir,
                    'path': str(path)
                })
        
        # Add /tmp if it exists (common for temporary files)
        if os.path.exists('/tmp') and os.path.isdir('/tmp'):
            common_dirs.append({
                'name': 'Temporary (/tmp)',
                'path': '/tmp'
            })
        
        return jsonify({
            'success': True,
            'data': {
                'directories': common_dirs
            }
        })
        
    except Exception as e:
        logger.error(f'Error getting common directories: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@bp.route('/api/filesystem/create-directory', methods=['POST'])
def create_directory():
    """
    Create a new directory at the specified path.
    
    Request:
        {
            "path": "/path/to/new/directory"
        }
    
    Response:
        {
            "success": true,
            "message": "Directory created successfully",
            "data": {
                "path": "/path/to/new/directory"
            }
        }
    """
    try:
        data = request.get_json() or {}
        path = data.get('path')
        
        if not path:
            return jsonify({
                'success': False,
                'message': 'Path is required'
            }), 400
        
        # Resolve to absolute path
        abs_path = os.path.abspath(path)
        
        # Security check
        if not is_safe_path(abs_path):
            return jsonify({
                'success': False,
                'message': 'Access to this directory is not allowed'
            }), 403
        
        # Check if already exists
        if os.path.exists(abs_path):
            return jsonify({
                'success': False,
                'message': 'Directory already exists'
            }), 409
        
        # Create directory (including parent directories)
        os.makedirs(abs_path, exist_ok=True)
        
        logger.info(f'Created directory: {abs_path}')
        
        return jsonify({
            'success': True,
            'message': 'Directory created successfully',
            'data': {
                'path': abs_path
            }
        })
        
    except PermissionError:
        return jsonify({
            'success': False,
            'message': 'Permission denied to create directory'
        }), 403
    except Exception as e:
        logger.error(f'Error creating directory: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
