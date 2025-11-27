from flask import Blueprint, request
from app.utils.response import success_response, error_response
from xhs_upload.auto_upload import XhsUploader
from conf import UPLOAD_FOLDER, OUTPUT_FOLDER, BASE_PATH
import os
import json
from datetime import datetime
from app.utils.logger import logger
from app.models.user import User
from app.models.note import Note
from app.models.image import Image
from app.extensions import db

bp = Blueprint('note', __name__, url_prefix='/api')

@bp.route('/publish', methods=['POST'])
def upload_note():
    try:
        logger.info("Starting note publish request")
        
        data = request.json
        title = data.get('title')
        desc = data.get('description')
        is_private = data.get('is_private', True)
        image_urls = data.get('images', [])
        topics = data.get('topics', [])
        user_id = data.get('userId')
        task_id = data.get('task_id')  # Advertisement task ID (optional)
        rule_card_id = data.get('rule_card_id')  # Rule card ID (optional)
        
        logger.info(f"Publish request - task_id: {task_id}, rule_card_id: {rule_card_id}")
        
        # Extract title from LLM-generated description and clean the content
        import re
        
        # Always extract title from description if it contains "标题："
        if desc:
            desc_lines = desc.strip().split('\n')
            cleaned_lines = []
            extracted_title = None
            
            for line in desc_lines:
                # Check if line contains "标题："
                title_match = re.match(r'^[#\s]*标题[：:]\s*(.+?)$', line.strip())
                if title_match:
                    extracted_title = title_match.group(1).strip()
                    # Skip this line - don't include it in the description
                    continue
                
                # Skip "正文：" line if present
                if re.match(r'^[#\s]*正文[：:]\s*$', line.strip()):
                    continue
                    
                cleaned_lines.append(line)
            
            # Use extracted title or fallback
            if extracted_title:
                title = extracted_title
                logger.info(f"Extracted title from description: {title}")
            elif not title or title == '小红书笔记':
                # Use first non-empty line as title
                for line in cleaned_lines:
                    if line.strip():
                        title = line.strip()[:50]
                        break
                logger.info(f"Using first line as title: {title}")
            
            # Update desc with cleaned content
            desc = '\n'.join(cleaned_lines).strip()
        
        logger.info(f"Note details - title: {title}, private: {is_private}, image count: {len(image_urls)}, topics: {topics}")
        
        if not all([title, image_urls, user_id]):
            logger.warning("Missing required fields in request")
            return error_response('Missing required fields: title, images, or userId')

        # 从数据库获取用户cookie
        user = User.query.get(user_id)
        if not user or not user.cookie:
            logger.error(f"User not found or no cookie available for user_id: {user_id}")
            return error_response('Invalid user or user cookie not available')

        # 验证并转换图片路径
        image_paths = []
        for url in image_urls:
            logger.info(f"Processing image URL: {url}")
            file_path = None
            
            # Handle ID-based URLs: /images/<id>/file or /api/images/<id>/file
            import re
            id_match = re.match(r'^(?:/api)?/images/(\d+)/file$', url)
            if id_match:
                image_id = int(id_match.group(1))
                image = Image.query.get(image_id)
                if image:
                    # Try local_path first, then file_path
                    for path in [image.local_path, image.file_path]:
                        if path and os.path.isfile(path):
                            file_path = path
                            break
                    if not file_path:
                        logger.error(f"Image file not found for ID {image_id}")
                        return error_response(f'Image file not found for ID: {image_id}')
                else:
                    logger.error(f"Image not found in database: ID {image_id}")
                    return error_response(f'Image not found: ID {image_id}')
            
            # Handle various URL path formats
            elif url.startswith('/images/upload/') or url.startswith('/images/uploads/'):
                filename = url.replace('/images/upload/', '', 1).replace('/images/uploads/', '', 1)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
            elif url.startswith('/images/output/'):
                filename = url.replace('/images/output/', '', 1)
                file_path = os.path.join(OUTPUT_FOLDER, filename)
            elif url.startswith('/images/local_dir/'):
                # For local_dir images, look up by filename in the database
                filename = url.replace('/images/local_dir/', '', 1)
                image = Image.query.filter(Image.filename == filename).first()
                if image and image.local_path and os.path.isfile(image.local_path):
                    file_path = image.local_path
                elif image and image.file_path and os.path.isfile(image.file_path):
                    file_path = image.file_path
                else:
                    # Try common locations
                    for base in [UPLOAD_FOLDER, OUTPUT_FOLDER, str(BASE_PATH)]:
                        test_path = os.path.join(base, filename)
                        if os.path.isfile(test_path):
                            file_path = test_path
                            break
            elif url.startswith('/images/'):
                # Generic /images/ path - try to find the file
                filename = url.replace('/images/', '', 1)
                for base in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
                    test_path = os.path.join(base, filename)
                    if os.path.isfile(test_path):
                        file_path = test_path
                        break
            elif os.path.isabs(url) and os.path.isfile(url):
                # Absolute path provided directly
                file_path = url
            else:
                logger.warning(f"Unrecognized image path format: {url}")
                return error_response(f'Invalid image path: {url}')

            if not file_path or not os.path.exists(file_path):
                logger.error(f"Image file not found: {url} -> {file_path}")
                return error_response(f'Image file not found: {url}')
                
            image_paths.append(file_path)
            logger.info(f"Validated image path: {file_path}")

        # 使用数据库中的cookie初始化上传器
        uploader = XhsUploader(user.cookie)
        formatted_topics = []
        desc_topic_tags = []
        
        for topic in topics:
            try:
                # Clean topic name: remove # prefix and content in parentheses
                ttpoc = topic.replace('#', '').strip()
                # Remove parentheses and content inside
                ttpoc_clean = re.sub(r'\([^)]*\)', '', ttpoc).strip()
                
                logger.info(f"Getting topic suggestions for: {ttpoc_clean} (original: {ttpoc})")
                
                suggest_result = uploader.xhs_client.get_suggest_topic(ttpoc_clean)
                
                if suggest_result and len(suggest_result) > 0:
                    # Use XHS suggested topic
                    topic_info = suggest_result[0]
                    suggested_name = topic_info.get('name')
                    
                    # Log if XHS suggested a different name
                    if suggested_name != ttpoc_clean:
                        logger.warning(f"⚠ XHS suggested different topic: '{ttpoc_clean}' → '{suggested_name}'")
                    else:
                        logger.info(f"✓ Got topic suggestion: {suggested_name} (ID: {topic_info.get('id')})")
                    
                    # Use original topic name if it's similar enough to avoid confusion
                    # Only use XHS suggested name if it's significantly different or empty
                    final_topic_name = ttpoc_clean if ttpoc_clean else suggested_name
                    
                    formatted_topics.append({
                        'id': topic_info.get('id'),
                        'name': final_topic_name,
                        'type': 'topic',
                        'link': topic_info.get('link')
                    })
                    
                    # Also format for description - XHS needs BOTH hashtags in text AND topics parameter
                    desc_topic_tags.append(f'#{final_topic_name}[话题]#')
                else:
                    # No suggestion found, use cleaned name as fallback
                    logger.warning(f"⚠ No suggestion for '{ttpoc_clean}', using as-is")
                    formatted_topics.append({
                        'id': '',
                        'name': ttpoc_clean,
                        'type': 'topic',
                        'link': ''
                    })
                    desc_topic_tags.append(f'#{ttpoc_clean}[话题]#')
                    
            except Exception as topic_error:
                logger.warning(f"✗ Failed topic lookup for '{ttpoc}': {topic_error}, using cleaned name")
                # Use cleaned name as fallback instead of skipping
                ttpoc_clean = re.sub(r'\([^)]*\)', '', topic.replace('#', '')).strip()
                if ttpoc_clean:
                    formatted_topics.append({
                        'id': '',
                        'name': ttpoc_clean,
                        'type': 'topic',
                        'link': ''
                    })
                    desc_topic_tags.append(f'#{ttpoc_clean}[话题]#')
        
        # XHS requires hashtags in BOTH description text AND topics parameter
        # Remove any existing hashtags first to avoid duplication
        desc = re.sub(r'#\S+', '', desc, flags=re.MULTILINE)  # Remove existing hashtags
        desc = re.sub(r'\n\s*\n+', '\n', desc).strip()  # Clean up empty lines
        
        # Append formatted topic tags to description
        final_desc = desc
        if desc_topic_tags:
            final_desc = desc + '\n' + ' '.join(desc_topic_tags)
        
        # Create note record in database
        note_record = Note(
            title=title,
            description=final_desc,
            image_paths=image_urls,
            topics=topics,
            is_private=is_private,
            user_id=user_id,
            status='publishing'
        )
        db.session.add(note_record)
        db.session.commit()
        
        logger.info(f"Created note record in database with ID: {note_record.id}")
        logger.info("========== XHS API REQUEST ==========")
        logger.info(f"Title: {title}")
        logger.info(f"Description: {final_desc}")
        logger.info(f"Images: {image_paths}")
        logger.info(f"Topics count: {len(formatted_topics)}")
        logger.info(f"Topics detail: {json.dumps(formatted_topics, ensure_ascii=False, indent=2)}")
        logger.info(f"Private: {is_private}")
        logger.info("=====================================")
        
        # Ensure topics list is not empty
        if not formatted_topics:
            logger.warning("⚠️ No valid topics found! Topics will not appear as blue labels.")
        
        note_response = uploader.upload_note(
            title=title,
            desc=final_desc,
            images=image_paths,
            topics=formatted_topics if formatted_topics else [],
            is_private=is_private
        )
        
        logger.info("========== XHS API RESPONSE ==========")
        logger.info(f"Response: {json.dumps(note_response, ensure_ascii=False, indent=2)}")
        logger.info("=======================================")
        
        # Update note record with response
        note_record.xhs_response = note_response
        note_record.note_id = note_response.get('note_id') or note_response.get('id')
        note_record.status = 'published'
        note_record.published_at = datetime.now()
        db.session.commit()
        
        logger.info(f"Successfully published note to XHS, DB ID: {note_record.id}, XHS ID: {note_record.note_id}")
        
        # Mark advertisement task as participated if task_id provided
        if task_id:
            try:
                from app.models.advertisement_task import AdvertisementTask
                task = AdvertisementTask.query.get(task_id)
                if task:
                    task.participated = True
                    task.participation_count = (task.participation_count or 0) + 1
                    task.last_participated_at = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"✓ Marked advertisement task {task_id} as participated")
                else:
                    logger.warning(f"⚠ Task {task_id} not found, skipping participation update")
            except Exception as task_error:
                logger.warning(f"⚠ Failed to update task participation status: {task_error}")
                # Don't fail the whole request if task update fails
        
        # Mark rule card as participated if rule_card_id provided
        if rule_card_id:
            try:
                from app.models.task_rule_card import TaskRuleCard
                rule_card = TaskRuleCard.query.get(rule_card_id)
                if rule_card:
                    rule_card.participated = True
                    rule_card.participation_count = (rule_card.participation_count or 0) + 1
                    rule_card.last_participated_at = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"✓ Marked rule card {rule_card_id} as participated")
                else:
                    logger.warning(f"⚠ Rule card {rule_card_id} not found, skipping participation update")
            except Exception as rule_card_error:
                logger.warning(f"⚠ Failed to update rule card participation status: {rule_card_error}")
                # Don't fail the whole request if rule card update fails
        
        return success_response({
            'note': note_response,
            'record_id': note_record.id,
            'note_id': note_record.note_id
        })
    
    
    except Exception as e:
        logger.exception("Error during note publishing")
        
        # Update note record if it exists
        try:
            if 'note_record' in locals():
                note_record.status = 'failed'
                note_record.error_message = str(e)
                db.session.commit()
                logger.info(f"Updated note record {note_record.id} status to failed")
        except Exception as db_error:
            logger.error(f"Failed to update note status in database: {db_error}")
        
        return error_response('Failed to publish note', 500)


@bp.route('/notes/list', methods=['GET'])
def list_notes():
    """List all published notes with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')  # Optional filter by status
        
        query = Note.query.order_by(Note.created_at.desc())
        
        if status:
            query = query.filter_by(status=status)
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        notes = [note.to_dict() for note in pagination.items]
        
        return success_response({
            'notes': notes,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
        
    except Exception as e:
        logger.exception("Error listing notes")
        return error_response(f'Failed to list notes: {str(e)}', 500)


@bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    try:
        note = Note.query.get(note_id)
        if not note:
            return error_response('Note not found', 404)
        
        return success_response(note.to_dict())
        
    except Exception as e:
        logger.exception(f"Error getting note {note_id}")
        return error_response(f'Failed to get note: {str(e)}', 500)