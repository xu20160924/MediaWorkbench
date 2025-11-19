from flask import Blueprint, request, send_from_directory, jsonify, current_app, make_response
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

# Create the blueprint with /api prefix to match frontend API calls
bp = Blueprint('image', __name__, url_prefix='/api')

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
        force_rescan = data.get('force_rescan', False)

        if not directory:
            return error_response('无效的目录路径')

        image_type_enum = None
        if image_type:
            try:
                image_type_enum = ImageType(image_type)
            except ValueError:
                image_type_enum = ImageType.general

        image_files = []
        for ext in ALLOWED_EXTENSIONS:
            image_files.extend(list(Path(directory).rglob(f'*.{ext}')))
        
        logger.info(f'Scanning directory: {directory}, found {len(image_files)} image files, type: {image_type_enum}, force_rescan: {force_rescan}')

        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        for img_path in image_files:
            # 先尝试通过本地路径匹配
            existing = Image.query.filter_by(local_path=str(img_path)).first()
            if existing:
                if image_type_enum and existing.image_type != image_type_enum:
                    existing.image_type = image_type_enum
                    updated_count += 1
                    logger.debug(f'Updated type for existing image: {img_path.name}')
                else:
                    skipped_count += 1
                continue

            # 再尝试通过文件名匹配，检查是否已存在同名图片
            filename = img_path.name
            found_duplicate = False
            possible_matches = Image.query.filter(Image.filename == filename).all()
            for rec in possible_matches:
                # 如果找到同名的local_dir记录，说明已存在，跳过
                if rec.source == ImageSource.local_dir:
                    found_duplicate = True
                    if image_type_enum and rec.image_type != image_type_enum:
                        rec.image_type = image_type_enum
                        updated_count += 1
                        logger.debug(f'Updated type for duplicate image: {filename}')
                    else:
                        skipped_count += 1
                    break
                # 如果是上传记录，更新其类型但不阻止创建local_dir记录
                elif image_type_enum and rec.image_type != image_type_enum:
                    p = (rec.file_path or '').replace('\\', '/').lower()
                    if 'upload/images/' in p or p.endswith(filename.lower()):
                        rec.image_type = image_type_enum
                        logger.debug(f'Updated type for uploaded image: {filename}')
            
            # 如果找到重复的local_dir记录，跳过
            if found_duplicate:
                continue

            img = Image(
                filename=img_path.name,
                file_path=str(img_path.relative_to(BASE_PATH)) if str(img_path).startswith(str(BASE_PATH)) else str(img_path),
                source=ImageSource.local_dir,
                local_path=str(img_path),
                image_type=image_type_enum or ImageType.general,
                created_at=datetime.fromtimestamp(img_path.stat().st_mtime)
            )
            db.session.add(img)
            added_count += 1
            logger.debug(f'Added new image: {img_path.name}')

        db.session.commit()
        
        logger.info(f'Scan complete: added={added_count}, updated={updated_count}, skipped={skipped_count}, total_files={len(image_files)}')

        return success_response({
            'message': f'扫描完成: 新增 {added_count} 张，更新 {updated_count} 张，跳过 {skipped_count} 张',
            'added_count': added_count,
            'updated_count': updated_count,
            'skipped_count': skipped_count,
            'total_files': len(image_files)
        })

    except Exception as e:
        logger.error(f'扫描目录失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return error_response('扫描目录失败')

@bp.route('/images/participate/<int:image_id>', methods=['POST'])
def mark_image_participation(image_id: int):
    """标记图片参与状态，使用 variables 中的 participated 字段进行存储"""
    try:
        payload = request.get_json() or {}
        participated = bool(payload.get('participated', True))

        image = Image.query.get_or_404(image_id)
        vars_obj = image.variables or {}
        # 仅允许广告规则类型标记参与
        try:
            image_type_value = image.image_type.value if hasattr(image.image_type, 'value') else image.image_type
        except Exception:
            image_type_value = image.image_type
        if image_type_value != ImageType.advertising_rule.value:
            return error_response('仅广告规则图片可参与', 400)

        vars_obj['participated'] = participated
        image.variables = vars_obj
        db.session.add(image)
        db.session.commit()

        return success_response(image.to_dict())
    except Exception as e:
        logger.error(f'标记参与状态失败: {str(e)}', exc_info=True)
        db.session.rollback()
        return error_response('标记参与状态失败')

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
        if not directory:
            return error_response('无效的目录路径')

        try:
            image_type_enum = ImageType(image_type)
        except ValueError:
            image_type_enum = ImageType.general

        existing = ImageDefaultLocation.query.filter_by(image_type=image_type_enum.value).first()
        if existing:
            existing.directory = directory
        else:
            existing = ImageDefaultLocation(image_type=image_type_enum.value, directory=directory)
            db.session.add(existing)
        db.session.commit()

        # After commit, the 'existing' object is persistent and can be converted to dict
        return success_response({'message': '默认目录已保存', 'location': existing.to_dict()})
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
            # Generate a filename for pasted images with microseconds for uniqueness
            import uuid
            import time
            # Use full timestamp with milliseconds to avoid collisions
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')  # Includes microseconds
            ext = file.mimetype.split('/')[-1] if '/' in file.mimetype else 'png'
            # Use full UUID to ensure absolute uniqueness
            unique_id = uuid.uuid4().hex
            file.filename = f'pasted_{timestamp}_{unique_id}.{ext}'
            logger.info(f"Generated unique filename for pasted image: {file.filename}")
            
        # Get image type from form data, default to 'general'
        image_type = request.form.get('image_type', 'general')
        try:
            # First try by name
            image_type_enum = ImageType(image_type)
        except ValueError:
            # Then try by value
            for member in ImageType:
                if member.value == image_type:
                    image_type_enum = member
                    break
            else:
                # If no match found, use default
                image_type_enum = ImageType.general
            
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            # Create upload directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Save the file to upload folder
            file.save(file_path)
            logger.info(f"File saved to upload folder: {file_path}")
            
            # Check if there's a default location for this image type
            default_location = ImageDefaultLocation.query.filter_by(
                image_type=image_type_enum.value
            ).first()
            
            local_path = None
            if default_location and default_location.directory:
                # Copy file to default directory
                try:
                    default_dir = default_location.directory
                    os.makedirs(default_dir, exist_ok=True)
                    
                    dest_path = os.path.join(default_dir, filename)
                    # If file already exists, add timestamp to make it unique
                    if os.path.exists(dest_path):
                        name, ext = os.path.splitext(filename)
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename_with_time = f"{name}_{timestamp}{ext}"
                        dest_path = os.path.join(default_dir, filename_with_time)
                    
                    shutil.copy2(file_path, dest_path)
                    local_path = dest_path
                    logger.info(f"File copied to default location: {dest_path}")
                except Exception as e:
                    logger.error(f"Failed to copy file to default location: {str(e)}")
                    # Continue even if copy fails
            
            # For pasted images (unique filenames), always create new records
            # For uploaded files with duplicate names, update existing record
            existing = Image.query.filter_by(source=ImageSource.upload, filename=filename).first()
            if existing and not filename.startswith('pasted_'):
                # Only update if it's a manually uploaded file (not pasted)
                logger.info(f"Updating existing image record for {filename}")
                existing.file_path = f'/uploads/{filename}'
                existing.image_type = image_type_enum
                existing.local_path = local_path
                image = existing
            else:
                # Always create new record for pasted images
                logger.info(f"Creating new image record for {filename} with type {image_type_enum}")
                image = Image(
                    filename=filename,
                    file_path=f'/uploads/{filename}',
                    source=ImageSource.upload,
                    image_type=image_type_enum,
                    local_path=local_path
                )
                db.session.add(image)
            db.session.commit()
            logger.info(f"Database committed. Image ID: {image.id}, Type: {image.image_type}, Local path: {local_path}")
            
            logger.info(f"Image uploaded successfully: {filename}")
            return success_response({
                'message': '图片上传成功' + (' (已保存到默认目录)' if local_path else ''),
                'image': image.to_dict()
            })
        else:
            return error_response('File type not allowed')
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error uploading image: {str(e)}", exc_info=True)
        return error_response(f'上传失败: {str(e)}')

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
                source=ImageSource.generated
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
        logger.info('list_images function called')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        logger.info(f'Page: {page}, Per page: {per_page}')
        
        query = Image.query
        
        # Filter by source if provided
        source = request.args.get('source')
        if source:
            # Normalize source to lowercase to match enum values
            source = source.lower()
            logger.info(f'Filtering by source: {source}')
            try:
                source_enum = ImageSource(source)
                logger.info(f'Converted source to enum: {source_enum}')
                query = query.filter(Image.source == source_enum)
            except Exception as e:
                logger.error(f'Error converting source to enum: {e}')
                query = query.filter(Image.source == source)
        
        # Filter by image type if provided
        image_type = request.args.get('image_type')
        if image_type:
            # Normalize image_type to lowercase to match enum values
            image_type = image_type.lower()
            logger.info(f'Filtering by image_type: {image_type}')
            try:
                image_type_enum = ImageType(image_type)
                logger.info(f'Converted image_type to enum: {image_type_enum}')
                query = query.filter(Image.image_type == image_type_enum)
            except Exception as e:
                logger.error(f'Error converting image_type to enum: {e}')
                query = query.filter(Image.image_type == image_type)
        
        # Paginate results
        logger.info('Executing query...')
        pagination = query.order_by(Image.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        logger.info(f'Query returned {pagination.total} results')
        
        logger.info('Converting results to dict...')
        images = [img.to_dict() for img in pagination.items]
        
        logger.info(f'Converted {len(images)} images to dict')
        
        response = success_response({
            'items': images,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
        logger.info(f'Returning response: {response}')
        return response
            
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        logger.error(f'获取图片列表失败: {str(e)}\n{tb_str}')
        return error_response(f'获取图片列表失败: {str(e)}', 500)

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

@bp.route('/images/output/<path:filename>')
@cross_origin()
def serve_output_file(filename):
    """Serve output/generated files"""
    try:
        from conf import OUTPUT_FOLDER
        
        # Use the configured output folder
        output_dir = os.path.abspath(OUTPUT_FOLDER)
        
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Log the file being served for debugging
        file_path = os.path.join(output_dir, filename)
        logger.info(f'Serving output file: {file_path}')
        
        if not os.path.exists(file_path):
            logger.error(f'Output file not found: {file_path}')
            return error_response(f'Output file not found: {filename}', 404)
            
        response = send_from_directory(output_dir, filename)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        logger.error(f'Error serving output file {filename}: {str(e)}', exc_info=True)
        return error_response(f'Error serving output file: {filename}', 500)

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
        if image.source == ImageSource.upload.value:
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
                        # Log error but continue to delete database record
                        logger.warning(f"Failed to delete file {filepath}: {str(e)}, but will continue to delete database record")
                else:
                    logger.warning(f"File not found: {filepath}, but will continue to delete database record")
        
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
        resp = make_response(error_response(f'删除图片失败: {str(e)}', 500))
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Credentials', 'true')
        return resp

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
        resp = make_response(error_response(f'清空图片失败: {str(e)}', 500))
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Credentials', 'true')
        return resp

@bp.route('/images/clear-local', methods=['DELETE'])
def clear_local_images():
    """清除所有本地目录图片记录（不删除实际文件）"""
    try:
        count = Image.query.filter_by(source=ImageSource.local_dir).delete()
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
            image_type_enum = ImageType.general

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
                Image.source == ImageSource.upload,
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
                if target.image_type != image_type_enum.value:
                    target.image_type = image_type_enum.value
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