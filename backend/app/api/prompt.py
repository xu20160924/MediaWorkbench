from flask import Blueprint, request
from app.utils.response import success_response, error_response
import openai
import json
import os
from conf import (
    OPENAI_API_KEY, 
    OPENAI_API_BASE, 
    BASE_PATH, 
    OPENAI_ENHANCE_MODEL,
    OPENAI_CAPTION_MODEL,
    PROMPT_ENHANCE_SYSTEM_MESSAGE,
    PROMPT_CAPTION_SYSTEM_MESSAGE,
)
from app.utils.logger import logger

bp = Blueprint('prompt', __name__, url_prefix='/api')

LLM_RUNTIME_CONFIG = {
    'enhance_model': OPENAI_ENHANCE_MODEL,
    'caption_model': OPENAI_CAPTION_MODEL,
    'api_base': OPENAI_API_BASE
}

@bp.route('/prompt/templates', methods=['GET'])
def list_prompt_templates():
    try:
        data = [
            {
                'id': 'enhance_system',
                'name': '提示词增强系统模板',
                'category': 'enhance',
                'tags': ['系统模板'],
                'content': PROMPT_ENHANCE_SYSTEM_MESSAGE,
            },
            {
                'id': 'caption_system',
                'name': '文案生成系统模板',
                'category': 'caption',
                'tags': ['系统模板'],
                'content': PROMPT_CAPTION_SYSTEM_MESSAGE,
            }
        ]
        return success_response(data)
    except Exception as e:
        logger.exception("Error listing prompt templates")
        return error_response('Failed to list prompt templates', 500)

@bp.route('/enhance-prompt', methods=['POST'])
def enhance_prompt():
    try:
        logger.info("Starting prompt enhancement request")
        
        prompt = request.json.get('prompt')
        if not prompt:
            logger.warning("Missing prompt in request")
            return error_response('Missing required field: prompt')

        logger.info(f"Processing prompt: {prompt[:100]}...")
        
        system_message = PROMPT_ENHANCE_SYSTEM_MESSAGE
        
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
        
        logger.info(f"Sending request to OpenAI API using model: {OPENAI_ENHANCE_MODEL}")
        response = client.chat.completions.create(
            model=OPENAI_ENHANCE_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"original image prompt：{prompt}"}
            ],
            temperature=0.65
        )
        
        content = response.choices[0].message.content.strip()
        logger.info("Successfully enhanced prompt")
        return success_response({'prompt': content})
            
    except Exception as e:
        logger.exception("Error during prompt enhancement")
        return error_response('Prompt enhancement failed', 500)

@bp.route('/generate-caption', methods=['POST'])
def generate_caption():
    try:
        logger.info("Starting caption generation request")
        
        prompt = request.json.get('prompt')
        if not prompt:
            logger.warning("Missing prompt in request")
            return error_response('Missing required field: prompt')

        logger.info(f"Processing prompt for caption: {prompt[:100]}...")
        
        system_message = PROMPT_CAPTION_SYSTEM_MESSAGE
        
        client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
        
        logger.info(f"Sending request to OpenAI API using model: {OPENAI_CAPTION_MODEL}")
        response = client.chat.completions.create(
            model=OPENAI_CAPTION_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"请根据以下描述生成小红书文案，记住必须返回JSON格式：{prompt}"}
            ],
            temperature=0.85,
            response_format={ "type": "json_object" }
        )
        
        content = json.loads(response.choices[0].message.content.strip())
        logger.info("Successfully generated caption")
        return success_response(content)
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
        return error_response(f'Invalid response format from OpenAI: {str(e)}', 500)
    except Exception as e:
        logger.exception("Error during caption generation")
        return error_response('Caption generation failed', 500)

@bp.route('/prompt/models', methods=['GET'])
def get_llm_models():
    try:
        return success_response({
            'enhance_model': LLM_RUNTIME_CONFIG.get('enhance_model'),
            'caption_model': LLM_RUNTIME_CONFIG.get('caption_model'),
            'api_base': LLM_RUNTIME_CONFIG.get('api_base'),
            'api_host': LLM_RUNTIME_CONFIG.get('api_host'),
            'api_port': LLM_RUNTIME_CONFIG.get('api_port')
        })
    except Exception as e:
        logger.exception('Error getting LLM models')
        return error_response('Failed to get LLM models', 500)

@bp.route('/prompt/models', methods=['POST'])
def set_llm_models():
    try:
        data = request.json or {}
        if 'enhance_model' in data:
            LLM_RUNTIME_CONFIG['enhance_model'] = data['enhance_model']
        if 'caption_model' in data:
            LLM_RUNTIME_CONFIG['caption_model'] = data['caption_model']
        if 'api_base' in data:
            LLM_RUNTIME_CONFIG['api_base'] = data['api_base']
        if 'api_host' in data:
            LLM_RUNTIME_CONFIG['api_host'] = data['api_host']
        if 'api_port' in data:
            LLM_RUNTIME_CONFIG['api_port'] = data['api_port']
        
        # Auto-construct api_base from host and port if both are provided
        if data.get('api_host') and data.get('api_port'):
            host = data['api_host']
            port = data['api_port']
            # Add http:// if no protocol specified
            if not host.startswith('http://') and not host.startswith('https://'):
                host = f'http://{host}'
            # Add /v1 suffix for OpenAI-compatible APIs (like Ollama)
            LLM_RUNTIME_CONFIG['api_base'] = f'{host}:{port}/v1'
            logger.info(f'Auto-constructed api_base: {LLM_RUNTIME_CONFIG["api_base"]}')
        
        return success_response(LLM_RUNTIME_CONFIG)
    except Exception as e:
        logger.exception('Error setting LLM models')
        return error_response('Failed to set LLM models', 500)

@bp.route('/prompt/participation', methods=['POST'])
def generate_participation_prompt():
    try:
        payload = request.json or {}
        regular_ids = payload.get('regular_image_ids', [])
        event_ids = payload.get('event_image_ids', [])
        rule_ids = payload.get('rule_image_ids')
        model = payload.get('model') or LLM_RUNTIME_CONFIG.get('enhance_model') or OPENAI_ENHANCE_MODEL
        
        # Get API base, filter out SOCKS proxies and invalid URLs
        api_base = LLM_RUNTIME_CONFIG.get('api_base')
        if api_base and ('socks' in api_base.lower() or not api_base.startswith('http') or 'your_openai' in api_base.lower()):
            logger.warning(f'Invalid or placeholder API base detected: {api_base}, ignoring')
            api_base = None
        
        # Check if we have a valid configuration
        if not api_base:
            error_msg = 'No valid API base URL configured. Please configure an LLM model in "LLM 模型管理" with a valid API Base (e.g., http://127.0.0.1:11434/v1 for Ollama)'
            logger.error(error_msg)
            return error_response(error_msg, 400)

        from app.models.image import Image, ImageType
        from app.api.static import serve_image
        from conf import UPLOAD_FOLDER, OUTPUT_FOLDER
        
        def build_url(img: Image):
            p = (img.file_path or '').replace('\\', '/').lower()
            if 'upload/' in p:
                suffix = p.split('upload/')[1]
                return f"/images/upload/{suffix}"
            if 'output/' in p:
                suffix = p.split('output/')[1]
                return f"/images/output/{suffix}"
            return ''

        selected = []
        if regular_ids:
            selected.extend(Image.query.filter(Image.id.in_(regular_ids)).all())
        if event_ids:
            selected.extend(Image.query.filter(Image.id.in_(event_ids)).all())
        rules = []
        if rule_ids:
            rules = Image.query.filter(Image.id.in_(rule_ids)).all()
        else:
            rules = Image.query.filter(Image.image_type == ImageType.advertising_rule.value).order_by(Image.created_at.desc()).limit(10).all()

        # Use API key if available, otherwise use a dummy key for Ollama
        api_key = OPENAI_API_KEY if OPENAI_API_KEY else "ollama"
        
        # Disable proxy by clearing environment variables
        import os
        for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
            os.environ.pop(proxy_var, None)
        
        # Create client - proxy should now be disabled
        client = openai.OpenAI(api_key=api_key, base_url=api_base)
        
        # Build text-only prompt (no images for now, as Ollama doesn't support vision)
        prompt_parts = []
        prompt_parts.append("请根据以下信息生成广告文案：")
        
        if selected:
            prompt_parts.append(f"\n已选择 {len(selected)} 张普通图片")
        if event_ids:
            prompt_parts.append(f"已选择 {len(event_ids)} 张活动图片")
        
        # 加入用户自定义提示词
        if 'custom_prompt' in payload and payload['custom_prompt']:
            prompt_parts.append(f"\n用户要求：{payload['custom_prompt']}")
        else:
            prompt_parts.append("\n请生成吸引人的广告文案，包含：参与目的、素材风格、文案要点、平台约束、需要避免的事项。")
        
        user_prompt = "\n".join(prompt_parts)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是广告参与提示词专家，需严格遵守规则图片中的限制。"},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6
        )
        content = response.choices[0].message.content.strip()
        return success_response({"prompt": content})
    except Exception as e:
        logger.exception('Error generating participation prompt')
        return error_response('Failed to generate participation prompt', 500)