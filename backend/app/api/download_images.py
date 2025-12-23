"""
API endpoints for downloading product images
"""
from flask import Blueprint, send_file, jsonify
import requests
import io
import zipfile
from app.models.buyer_task import BuyerTask
from app.extensions import db

download_images_bp = Blueprint('download_images', __name__)

@download_images_bp.route('/api/buyer-tasks/<int:task_id>/download-images', methods=['GET'])
def download_buyer_task_images(task_id):
    """Download all images for a buyer task as a ZIP file"""
    try:
        # Get the buyer task
        task = db.session.get(BuyerTask, task_id)
        if not task:
            return jsonify({'success': False, 'message': 'Task not found'}), 404
        
        if not task.small_images or len(task.small_images) == 0:
            return jsonify({'success': False, 'message': 'No images found for this task'}), 404
        
        # Create a ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, image_url in enumerate(task.small_images):
                try:
                    # Download the image
                    response = requests.get(image_url, timeout=30)
                    response.raise_for_status()
                    
                    # Determine file extension from URL or content-type
                    content_type = response.headers.get('content-type', '')
                    if 'jpeg' in content_type or 'jpg' in content_type:
                        ext = 'jpg'
                    elif 'png' in content_type:
                        ext = 'png'
                    elif 'webp' in content_type:
                        ext = 'webp'
                    else:
                        # Try to get from URL
                        if image_url.endswith('.jpg') or image_url.endswith('.jpeg'):
                            ext = 'jpg'
                        elif image_url.endswith('.png'):
                            ext = 'png'
                        elif image_url.endswith('.webp'):
                            ext = 'webp'
                        else:
                            ext = 'jpg'  # default
                    
                    # Add to ZIP with a numbered filename
                    filename = f"{idx + 1:02d}.{ext}"
                    zip_file.writestr(filename, response.content)
                    
                except Exception as e:
                    print(f"Failed to download image {idx + 1}: {str(e)}")
                    # Continue with other images
                    continue
        
        # Seek to the beginning of the BytesIO buffer
        zip_buffer.seek(0)
        
        # Create a safe filename from task title
        safe_title = "".join(c for c in task.task_title if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title[:50]  # Limit length
        if not safe_title:
            safe_title = f"buyer_task_{task_id}"
        
        zip_filename = f"{safe_title}_images.zip"
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to download images: {str(e)}'
        }), 500
