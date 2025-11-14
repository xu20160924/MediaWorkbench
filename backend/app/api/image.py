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
from app.models.image import Image, ImageSource, ImageType, ImageDefaultLocation
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
    """扫描指定目录并添加图片到数据库，可选指定图片类型"""
    try:
        data = request.get_json()
        directory = data.get('directory')
        image_type = data.get('image_type')

        if not directory or not os.path.isdir(directory):
            return error_response('无效的目录路径')

        image_type_enum = None
        if image_type:
            try:
                image_type_enum = ImageType(image_type)
            except ValueError:
                image_type_enum = ImageType.GENERAL

        image_files = []
        for ext in ALLOWED_EXTENSIONS:
            image_files.extend(list(Path(directory).rglob(f'*.{ext}')))

        added_count = 0
        for img_path in image_files:
            # 先尝试通过本地路径匹配
            existing = Image.query.filter_by(local_path=str(img_path)).first()
            if existing:
                if image_type_enum and existing.image_type != image_type_enum:
                    existing.image_type = image_type_enum
                continue

            # 再尝试通过文件名匹配上传记录并纠正类型
            filename = img_path.name
            possible_matches = Image.query.filter(Image.filename == filename).all()
            for rec in possible_matches:
                if image_type_enum and rec.image_type != image_type_enum:
                    # 仅在上传目录或同一默认目录下进行纠正
                    p = (rec.file_path or '').replace('\\', '/').lower()
                    if 'upload/images/' in p or p.endswith(filename.lower()):
                        rec.image_type = image_type_enum

            img = Image(
                filename=img_path.name,
                file_path=str(img_path.relative_to(BASE_PATH)) if str(img_path).startswith(str(BASE_PATH)) else str(img_path),
                source=ImageSource.LOCAL_DIR,
                local_path=str(img_path),
                image_type=image_type_enum or ImageType.GENERAL,
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

@bp.route('/images/default-locations', methods=['GET'])
def list_default_locations():
    try:
        items = ImageDefaultLocation.query.all()
        return success_response([i.to_dict() for i in items])
    except Exception as e:
        logger.error(f'获取默认目录失败: {str(e)}', exc_info=True)
        return error_response('获取默认目录失败')

@bp.route('/images/default-location', methods=['POST'])
def set_default_location():
    """设置某图片类型的默认目录，并立即进行扫描加载"""
    try:
        data = request.get_json() or {}
        image_type = data.get('image_type')
        directory = data.get('directory')

        if not image_type:
            return error_response('缺少图片类型')
        if not directory or not os.path.isdir(directory):
            return error_response('无效的目录路径')

        try:
            image_type_enum = ImageType(image_type)
        except ValueError:
            image_type_enum = ImageType.GENERAL

        existing = ImageDefaultLocation.query.filter_by(image_type=image_type_enum.value).first()
        if existing:
            existing.directory = directory
        else:
            existing = ImageDefaultLocation(image_type=image_type_enum.value, directory=directory)
            db.session.add(existing)
        db.session.commit()

        try:
            image_files = []
            for ext in ALLOWED_EXTENSIONS:
                image_files.extend(list(Path(directory).rglob(f'*.{ext}')))

            added_count = 0
            for img_path in image_files:
                existing = Image.query.filter_by(local_path=str(img_path)).first()
                if existing:
                    if image_type_enum and existing.image_type != image_type_enum:
                        existing.image_type = image_type_enum
                    continue
                # 纠正上传记录的类型
                filename = img_path.name
                possible_matches = Image.query.filter(Image.filename == filename).all()
                for rec in possible_matches:
                    if image_type_enum and rec.image_type != image_type_enum:
                        p = (rec.file_path or '').replace('\\', '/').lower()
                        if 'upload/images/' in p or p.endswith(filename.lower()):
                            rec.image_type = image_type_enum
                img = Image(
                    filename=img_path.name,
                    file_path=str(img_path.relative_to(BASE_PATH)) if str(img_path).startswith(str(BASE_PATH)) else str(img_path),
                    source=ImageSource.LOCAL_DIR,
                    local_path=str(img_path),
                    image_type=image_type_enum,
                    created_at=datetime.fromtimestamp(img_path.stat().st_mtime)
                )
                db.session.add(img)
                added_count += 1
            db.session.commit()
        except Exception as se:
            logger.error(f'扫描默认目录失败: {str(se)}', exc_info=True)
            db.session.rollback()
            return error_response('保存成功，但扫描目录失败')

        return success_response({'message': '默认目录已保存并加载', 'added_count': added_count, 'location': existing.to_dict()})
    except Exception as e:
        logger.error(f'设置默认目录失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return error_response('设置默认目录失败')

@bp.route('/images/base-paths', methods=['GET'])
def get_base_paths():
    try:
        return success_response({
            'upload_folder': UPLOAD_FOLDER,
            'output_folder': OUTPUT_FOLDER
        })
    except Exception as e:
        logger.error(f'获取基础路径失败: {str(e)}', exc_info=True)
        return error_response('获取基础路径失败')

@bp.route('/images/upload', methods=['POST'])
def upload_image():
    try:
        logger.info("Starting image upload request")
        
        if 'file' not in request.files:
            logger.warning("No file part in the request")
            return error_response('No file part')
            
        file = request.files['file']
        if file.filename == '':
            return error_response('No selected file')
            
        # Get image type from form data, default to 'general'
        image_type = request.form.get('image_type', 'general')
        try:
            image_type_enum = ImageType(image_type)
        except ValueError:
            image_type_enum = ImageType.GENERAL
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # Create upload directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save the file
            file.save(file_path)
            
            # Deduplicate by filename for uploads
            existing = Image.query.filter_by(source=ImageSource.UPLOAD, filename=filename).first()
            if existing:
                existing.file_path = f'/uploads/{filename}'
                existing.image_type = image_type_enum
                image = existing
            else:
                image = Image(
                    filename=filename,
                    file_path=f'/uploads/{filename}',
                    source=ImageSource.UPLOAD,
                    image_type=image_type_enum
                )
                db.session.add(image)
            db.session.commit()
            
            logger.info(f"Image uploaded successfully: {filename}")
            return success_response({
                'message': '图片上传成功',
                'image': image.to_dict()
            })
        else:
            return error_response('File type not allowed')
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading image: {str(e)}", exc_info=True)
        return error_response(f'上传失败: {str(e)}')
        
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
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = Image.query
        
        # Filter by source if provided
        source = request.args.get('source')
        if source:
            try:
                source_enum = ImageSource(source)
                query = query.filter(Image.source == source_enum)
            except Exception:
                query = query.filter(Image.source == source)
        
        # Filter by image type if provided
        image_type = request.args.get('image_type')
        if image_type:
            try:
                image_type_enum = ImageType(image_type)
                query = query.filter(Image.image_type == image_type_enum)
            except Exception:
                query = query.filter(Image.image_type == image_type)
        
        # Paginate results
        pagination = query.order_by(Image.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        images = [img.to_dict() for img in pagination.items]
        
        return success_response({
            'items': images,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
            
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
            p = str(image.file_path or '').replace('\\', '/')
            filename = None
            if p.startswith('/uploads/'):
                filename = p.split('/uploads/')[1]
            elif 'upload/images/' in p or p.startswith('upload/images/'):
                filename = p.split('upload/images/')[1]

            if filename:
                filepath = os.path.join(UPLOAD_FOLDER, filename)
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

@bp.route('/images/clear-all', methods=['DELETE', 'OPTIONS'])
@cross_origin()
def clear_all_images():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        logger.info('Received request to clear all images')
        images = Image.query.all()
        deleted_count = 0

        for image in images:
            try:
                p = str(image.file_path).replace('\\', '/') if image.file_path else ''
                if p:
                    if p.startswith('/uploads/') or '/upload/images/' in p or p.startswith('upload/images/'):
                        filename = None
                        if p.startswith('/uploads/'):
                            filename = p.split('/uploads/')[1]
                        elif 'upload/images/' in p or p.startswith('upload/images/'):
                            filename = p.split('upload/images/')[1]
                        if filename:
                            target = os.path.join(UPLOAD_FOLDER, filename)
                            if os.path.exists(target):
                                os.remove(target)
                    elif 'output/images/' in p or p.startswith('/output/') or p.startswith('output/'):
                        filename = None
                        if 'output/images/' in p:
                            filename = p.split('output/images/')[1]
                        elif p.startswith('/output/'):
                            filename = p.split('/output/')[1]
                        elif p.startswith('output/'):
                            filename = p.split('output/')[1]
                        if filename:
                            target = os.path.join(OUTPUT_FOLDER, filename)
                            if os.path.exists(target):
                                os.remove(target)
            except Exception as fe:
                logger.error(f'Failed to delete file for image {image.id}: {str(fe)}')

            db.session.delete(image)
            deleted_count += 1

        db.session.commit()
        response = success_response({'message': '已删除所有图片', 'count': deleted_count})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    except Exception as e:
        logger.error(f'清空图片失败: {str(e)}', exc_info=True)
        db.session.rollback()
        response = error_response(f'清空图片失败: {str(e)}', 500)
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

@bp.route('/images/reclassify', methods=['POST'])
def reclassify_images():
    """将指定目录下的所有图片记录统一调整为给定类型（同时纠正上传记录同名文件）"""
    try:
        data = request.get_json() or {}
        directory = data.get('directory')
        image_type = data.get('image_type')

        if not directory or not os.path.isdir(directory):
            return error_response('无效的目录路径')
        try:
            image_type_enum = ImageType(image_type)
        except Exception:
            image_type_enum = ImageType.GENERAL

        # 1) 纠正本地记录（local_dir）在该目录下的类型
        count_local = 0
        local_records = Image.query.filter(
            Image.local_path.like(f"{directory}%")
        ).all()
        for rec in local_records:
            if rec.image_type != image_type_enum:
                rec.image_type = image_type_enum
                count_local += 1

        # 2) 收集目录下文件名，纠正上传记录（upload）同名文件的类型
        filenames = set(p.name for p in Path(directory).rglob('*') if p.is_file())
        count_upload = 0
        if filenames:
            upload_records = Image.query.filter(
                Image.source == ImageSource.UPLOAD,
                Image.filename.in_(list(filenames))
            ).all()
            # unify duplicates by filename, prefer non-general type
            by_name: Dict[str, List[Image]] = {}
            for rec in upload_records:
                by_name.setdefault(rec.filename, []).append(rec)
            for name, group in by_name.items():
                target = None
                for rec in group:
                    if rec.image_type == image_type_enum:
                        target = rec
                        break
                if target is None:
                    target = max(group, key=lambda r: r.id)
                for rec in group:
                    if rec.id != target.id:
                        db.session.delete(rec)
                if target.image_type != image_type_enum:
                    target.image_type = image_type_enum
                count_upload += len(group)

        db.session.commit()
        return success_response({
            'message': '类型纠正完成',
            'updated_local': count_local,
            'updated_upload': count_upload
        })
    except Exception as e:
        logger.error(f'类型纠正失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return error_response('类型纠正失败')