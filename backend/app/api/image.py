from flask import Blueprint, request, send_from_directory, jsonify, current_app
from flask_cors import cross_origin
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional

from app.utils.response import success_response, error_response
from conf import ALLOWED_EXTENSIONS, UPLOAD_FOLDER, OUTPUT_FOLDER, BASE_PATH
from comfyui_api.utils.actions.prompt_to_image import prompt_to_image
from comfyui_api.utils.actions.load_workflow import load_workflow
from app.models.image import Image, ImageSource
from app.extensions import db
from app.utils.logger import logger
from app.models.workflow import Workflow
from app.models.variable_definitions import VariableDefinitions
from app.models.workflow_variable import WorkflowVariable

# Create the blueprint without the URL prefix since it's already added in __init__.py
bp = Blueprint('image', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/images/scan-directory', methods=['POST'])
def scan_image_directory():
    """扫描指定目录并添加图片到数据库"""
    try:
        data = request.get_json()
        directory = data.get('directory')
        
        if not directory or not os.path.isdir(directory):
            return error_response('无效的目录路径')
            
        # 获取目录中的所有图片文件
        image_files = []
        for ext in ALLOWED_EXTENSIONS:
            image_files.extend(list(Path(directory).rglob(f'*.{ext}')))
            
        added_count = 0
        for img_path in image_files:
            # 检查是否已存在
            existing = Image.query.filter_by(local_path=str(img_path)).first()
            if existing:
                continue
                
            # 创建新的图片记录
            img = Image(
                filename=img_path.name,
                file_path=str(img_path.relative_to(BASE_PATH)) if str(img_path).startswith(str(BASE_PATH)) else str(img_path),
                source=ImageSource.LOCAL_DIR,
                local_path=str(img_path),
                created_at=datetime.fromtimestamp(img_path.stat().st_mtime)
            )
            db.session.add(img)
            added_count += 1
            
        db.session.commit()
        
        return success_response({
            'message': f'成功添加 {added_count} 张图片',
            'added_count': added_count
        })
        
    except Exception as e:
        logger.error(f'扫描目录失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return error_response('扫描目录失败')

@bp.route('/images/upload', methods=['POST'])
def upload_image():
    try:
        logger.info("Starting image upload request")
        
        if 'file' not in request.files:
            logger.warning("No file part in the request")
            return error_response('请选择要上传的文件')
            
        file = request.files['file']
        
        if file.filename == '':
            logger.warning("No file selected")
            return error_response('请选择要上传的文件')
            
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return error_response(f'File type not allowed. Allowed types are: {", ".join(ALLOWED_EXTENSIONS)}')
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存文件
        file.save(filepath)
        
        # 保存到数据库
        image = Image(
            filename=filename,
            file_path=os.path.join('uploads', filename),
            source=ImageSource.UPLOAD
        )
        db.session.add(image)
        db.session.commit()
        
        logger.info(f"Image uploaded successfully: {filename}")
        return success_response({
            'message': '图片上传成功',
            'image': image.to_dict()
        })
        
    except Exception as e:
        logger.error(f'上传图片失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return error_response('上传图片失败')

@bp.route('/images/generate', methods=['POST'])
def generate_image():
    try:
        logger.info("Starting image generation request")
        
        data = request.json
        workflow_id = data.get('workflow_id')
        variables = data.get('variables', [])
        output_vars = data.get('output_vars', [])
        
        if not workflow_id:
            logger.warning("Missing workflow_id in request")
            return error_response('Missing required field: workflow_id')
            
        # 获取工作流信息
        workflow = Workflow.query.get_or_404(workflow_id)
        
        # 规范化路径处理
        normalized_path = workflow.file_path.replace('\\', '/')
        workflow_path = os.path.join(BASE_PATH, normalized_path)
        
        if not os.path.exists(workflow_path):
            logger.error(f"Workflow file not found: {workflow_path}")
            return error_response('Workflow file not found')
            
        # 加载工作流
        logger.info(f"Loading workflow from: {workflow_path}")
        workflow_data = load_workflow(workflow_path)
        
        # 构建变量映射
        variable_mapping = {}
        for var in variables:
            var_id = var.get('id')
            value = var.get('value')
            
            workflow_var = WorkflowVariable.query.filter_by(
                workflow_id=workflow_id,
                id=var_id
            ).first()
            
            if workflow_var:
                var_def = VariableDefinitions.query.get(workflow_var.class_type_id)
                if var_def:
                    # 构建新的变量映射格式：{node_id: {value_path: value}}
                    if workflow_var.node_id not in variable_mapping:
                        variable_mapping[workflow_var.node_id] = {}
                    variable_mapping[workflow_var.node_id][var_def.value_path] = value
        
        # 获取输出节点信息
        output_nodes = []
        for output_id in output_vars:
            workflow_var = WorkflowVariable.query.filter_by(
                workflow_id=workflow_id,
                id=output_id
            ).first()
            if workflow_var:
                output_nodes.append(workflow_var.node_id)
        
        logger.info(f"Variable mapping created: {variable_mapping}")
        logger.info(f"Output nodes: {output_nodes}")
        
        # 调用生成方法
        logger.info("Starting image generation process")
        try:
            result = prompt_to_image(
                workflow=workflow_data,
                variable_values=variable_mapping,
                output_node_ids=output_nodes,
                save_previews=True
            )
        except ValueError as e:
            logger.error("Invalid input parameters", exc_info=e)
            return error_response(str(e), 400)
        except RuntimeError as e:
            logger.error("Image generation failed", exc_info=e)
            return error_response(str(e), 500)
            
        logger.info(f"Image generation completed: {result}")
        
        # 保存图片信息到数据库
        try:
            image = Image(
                filename=os.path.basename(result[0]),
                workflow_id=workflow_id,
                workflow_name=workflow.name,
                file_path=os.path.join(OUTPUT_FOLDER, result[0]),
                variables=variable_mapping,
                source=ImageSource.GENERATED
            )
            db.session.add(image)
            db.session.commit()
            logger.info(f"Image record saved to database with ID: {image.id}")
        except Exception as e:
            logger.error("Failed to save image record to database", exc_info=e)
            # 即使数据库保存失败，仍然返回生成的图片
            return success_response({
                'message': 'Image generated but failed to save record',
                'result': result,
                'error': str(e)
            })

        return success_response({
            'message': 'Image generated successfully',
            'result': result,
            'image_info': image.to_dict()
        })

    except Exception as e:
        logger.exception("Unexpected error during image generation")
        return error_response(f'Image generation failed: {str(e)}', 500)

@bp.route('/images', methods=['GET'])
def list_images():
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 获取筛选参数
        workflow_id = request.args.get('workflow_id', type=int)
        source = request.args.get('source')  # 'upload' or 'local_dir'
        
        # 构建查询
        query = Image.query
        
        if workflow_id is not None:
            query = query.filter_by(workflow_id=workflow_id)
            
        if source in [s.value for s in ImageSource]:
            query = query.filter(Image.source == source)
        
        # 按创建时间降序排序
        query = query.order_by(Image.created_at.desc())
        
        # 分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        images = pagination.items
        
        # 构建返回数据
        result = {
            'items': [image.to_dict() for image in images],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        }
        
        return success_response(result)
        
    except Exception as e:
        logger.error(f'获取图片列表失败: {str(e)}', exc_info=True)
        return error_response('获取图片列表失败')

@bp.route('/images/<int:image_id>', methods=['GET'])
def get_image(image_id):
    try:
        image = Image.query.get_or_404(image_id)
        return success_response(image.to_dict())
    except Exception as e:
        logger.exception(f"Error while retrieving image {image_id}")
        return error_response('Failed to retrieve image details', 500)

@bp.route('/images/uploads/<path:filename>')
@cross_origin()
def serve_uploaded_file(filename):
    """Serve uploaded files"""
    try:
        from conf import UPLOAD_FOLDER
        
        # Use the configured upload folder
        uploads_dir = os.path.abspath(UPLOAD_FOLDER)
        
        # Ensure the uploads directory exists
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Log the file being served for debugging
        file_path = os.path.join(uploads_dir, filename)
        logger.info(f'Serving file: {file_path}')
        
        if not os.path.exists(file_path):
            logger.error(f'File not found: {file_path}')
            return error_response(f'File not found: {filename}', 404)
            
        response = send_from_directory(uploads_dir, filename)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        logger.error(f'Error serving file {filename}: {str(e)}', exc_info=True)
        return error_response(f'Error serving file: {filename}', 500)

@bp.route('/images/delete/<int:image_id>', methods=['DELETE', 'OPTIONS'])
@cross_origin()
def delete_image(image_id):
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    try:
        logger.info(f"Received DELETE request for image ID: {image_id}")
        image = Image.query.get_or_404(image_id)
        logger.info(f"Found image: {image_id}, path: {image.file_path}, source: {image.source}")
        
        # 只删除上传的文件，不删除本地目录中的文件
        if image.source == ImageSource.UPLOAD:
            filepath = os.path.join(BASE_PATH, image.file_path)
            logger.info(f"Attempting to delete file: {filepath}")
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.info(f"Successfully deleted file: {filepath}")
                except Exception as e:
                    logger.error(f"Failed to delete file {filepath}: {str(e)}")
                    return error_response(f'删除文件失败: {str(e)}', 500)
        
        # 删除数据库记录
        db.session.delete(image)
        db.session.commit()
        
        response = success_response({'message': '图片删除成功'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
        
    except Exception as e:
        logger.error(f'删除图片失败: {str(e)}', exc_info=True)
        db.session.rollback()
        response = error_response(f'删除图片失败: {str(e)}', 500)
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

@bp.route('/images/clear-local', methods=['DELETE'])
def clear_local_images():
    """清除所有本地目录图片记录（不删除实际文件）"""
    try:
        count = Image.query.filter_by(source=ImageSource.LOCAL_DIR).delete()
        db.session.commit()
        return success_response({
            'message': f'已清除 {count} 条本地目录图片记录',
            'count': count
        })
    except Exception as e:
        logger.error(f'清除本地图片记录失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return error_response('清除本地图片记录失败')