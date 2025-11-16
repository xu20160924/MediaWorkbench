from flask import Blueprint, send_from_directory
import os
from app.utils.response import error_response
from conf import UPLOAD_FOLDER, OUTPUT_FOLDER
from app.utils.logger import logger

bp = Blueprint('static', __name__, url_prefix='/api')

@bp.route('/images/<path:filename>')
def serve_image(filename):
    try:
        logger.info(f"Serving image request: {filename}")
        
        # Try to serve the file with the 'Online_AI_' prefix first (for uploaded files)
        if filename.startswith('upload/'):
            # Handle both with and without Online_AI_ prefix
            actual_filename = filename[7:]  # Remove 'upload/' prefix
            upload_image_path = os.path.join(UPLOAD_FOLDER, actual_filename)
            logger.info(f"Checking direct upload image path: {upload_image_path}")
            
            # Try the direct path first
            if os.path.exists(upload_image_path):
                logger.info(f"Serving direct upload image from: {upload_image_path}")
                return send_from_directory(UPLOAD_FOLDER, actual_filename)
            
            # If not found, try with Online_AI_ prefix
            prefixed_filename = f"Online_AI_{actual_filename}"
            prefixed_image_path = os.path.join(UPLOAD_FOLDER, prefixed_filename)
            logger.info(f"Checking prefixed upload image path: {prefixed_image_path}")
            
            if os.path.exists(prefixed_image_path):
                logger.info(f"Serving prefixed upload image from: {prefixed_image_path}")
                return send_from_directory(UPLOAD_FOLDER, prefixed_filename)
    
        elif filename.startswith('output/'):
            # Frontend is asking for /images/output/filename, but the actual path is OUTPUT_FOLDER/filename
            actual_filename = filename[7:]  # Remove 'output/' prefix
            output_image_path = os.path.join(OUTPUT_FOLDER, actual_filename)
            logger.info(f"Checking output image path: {output_image_path}")
            
            if os.path.exists(output_image_path):
                logger.info(f"Serving output image from: {output_image_path}")
                return send_from_directory(os.path.dirname(output_image_path), os.path.basename(output_image_path))
        
        # Fallback: try to serve directly from the requested path
        for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
            full_path = os.path.join(folder, filename)
            if os.path.exists(full_path):
                logger.info(f"Serving image from direct path: {full_path}")
                return send_from_directory(folder, filename)
            
            # Try with Online_AI_ prefix as a last resort
            prefixed_path = os.path.join(folder, f"Online_AI_{filename}")
            if os.path.exists(prefixed_path):
                logger.info(f"Serving image with Online_AI_ prefix: {prefixed_path}")
                return send_from_directory(folder, f"Online_AI_{filename}")
        
        logger.warning(f"Image not found at any path: {filename}")
        return error_response('Image not found', 404)
    except Exception as e:
        logger.exception(f"Error serving image: {filename}")
        return error_response('Image not found', 404)