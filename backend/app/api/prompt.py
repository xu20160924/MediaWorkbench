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
    'api_base': OPENAI_API_BASE,
    'provider': 'openai',
}

@bp.route('/prompt/templates', methods=['GET'])
def list_prompt_templates():
    try:
        data = []
        return success_response(data)
    except Exception as e:
        logger.exception("Error listing prompt templates")
        return error_response('Failed to list prompt templates', 500)

@bp.route('/prompt/ollama-status', methods=['GET'])
def check_ollama_status():
    """Check Ollama service status and available models"""
    import requests as req
    
    api_base = LLM_RUNTIME_CONFIG.get('api_base', '')
    ollama_base = api_base.replace('/v1', '').rstrip('/') if api_base else 'http://127.0.0.1:11434'
    
    result = {
        'configured_api_base': api_base,
        'ollama_base': ollama_base,
        'ollama_reachable': False,
        'models': [],
        'configured_model': LLM_RUNTIME_CONFIG.get('enhance_model', OPENAI_ENHANCE_MODEL),
        'error': None
    }
    
    try:
        # Check if Ollama is running
        tags_url = f"{ollama_base}/api/tags"
        response = req.get(tags_url, timeout=5)
        
        if response.ok:
            result['ollama_reachable'] = True
            models_data = response.json().get('models', [])
            result['models'] = [m.get('name', '') for m in models_data]
            
            # Check if configured model exists
            configured_model = result['configured_model']
            model_base = configured_model.split(':')[0] if ':' in configured_model else configured_model
            result['model_available'] = any(model_base in m for m in result['models'])
            
            if not result['model_available']:
                result['error'] = f"Model '{configured_model}' not found. Run: ollama pull {configured_model}"
        else:
            result['error'] = f"Ollama returned HTTP {response.status_code}"
            
    except req.exceptions.ConnectionError:
        result['error'] = f"Cannot connect to Ollama at {ollama_base}. Run: ollama serve"
    except req.exceptions.Timeout:
        result['error'] = "Ollama connection timed out"
    except Exception as e:
        result['error'] = str(e)
    
    return success_response(result)

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
            'api_port': LLM_RUNTIME_CONFIG.get('api_port'),
            'provider': LLM_RUNTIME_CONFIG.get('provider', 'openai'),
        })
    except Exception as e:
        logger.exception('Error getting LLM models')
        return error_response('Failed to get LLM models', 500)

@bp.route('/prompt/models', methods=['POST'])
def set_llm_models():
    try:
        data = request.json or {}
        
        logger.info("=" * 80)
        logger.info(" UPDATING LLM RUNTIME CONFIG")
        logger.info("=" * 80)
        logger.info(f" Received config update: {json.dumps(data, indent=2, ensure_ascii=False)}")
        logger.info(f" Current config BEFORE update: {json.dumps(LLM_RUNTIME_CONFIG, indent=2, ensure_ascii=False)}")
        
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
        if 'provider' in data:
            LLM_RUNTIME_CONFIG['provider'] = data['provider']
        
        # Auto-construct api_base from host and port if both are provided
        if data.get('api_host') and data.get('api_port'):
            host = data['api_host']
            port = data['api_port']
            # Add http:// if no protocol specified
            if not host.startswith('http://') and not host.startswith('https://'):
                host = f'http://{host}'
            # Add /v1 suffix for OpenAI-compatible APIs (like Ollama)
            LLM_RUNTIME_CONFIG['api_base'] = f'{host}:{port}/v1'
            logger.info(f'✨ Auto-constructed api_base: {LLM_RUNTIME_CONFIG["api_base"]}')
        
        logger.info(f"✅ Updated config AFTER update: {json.dumps(LLM_RUNTIME_CONFIG, indent=2, ensure_ascii=False)}")
        logger.info("=" * 80)
        
        return success_response(LLM_RUNTIME_CONFIG)
    except Exception as e:
        logger.error("=" * 80)
        logger.error(" ERROR SETTING LLM MODELS")
        logger.error("=" * 80)
        logger.exception('Error setting LLM models')
        logger.error("=" * 80)
        return error_response('Failed to set LLM models', 500)

@bp.route('/prompt/participation', methods=['POST'])
def generate_participation_prompt():
    try:
        payload = request.json or {}
        logger.info("=" * 80)
        logger.info(" PARTICIPATION PROMPT REQUEST START")
        logger.info("=" * 80)
        logger.info(f" Complete Request Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        regular_ids = payload.get('regular_image_ids', [])
        event_ids = payload.get('event_image_ids', [])
        rule_ids = payload.get('rule_image_ids', [])
        model = payload.get('model') or LLM_RUNTIME_CONFIG.get('enhance_model') or OPENAI_ENHANCE_MODEL
        
        logger.info(f" Parsed Data:")
        logger.info(f"  - Regular Image IDs: {regular_ids}")
        logger.info(f"  - Event Image IDs: {event_ids}")
        logger.info(f"  - Rule Image IDs: {rule_ids}")
        logger.info(f"  - Model: {model}")
        
        # Get provider from config first to determine validation
        provider = LLM_RUNTIME_CONFIG.get('provider', 'openai')
        logger.info(f" LLM Provider: {provider}")
        
        # Get API base
        api_base = LLM_RUNTIME_CONFIG.get('api_base')
        logger.info(f" API Base (from config): {api_base}")
        
        if api_base and ('socks' in api_base.lower() or not api_base.startswith('http') or 'your_openai' in api_base.lower()):
            logger.warning(f'  Invalid or placeholder API base detected: {api_base}, ignoring')
            api_base = None
        
        # Require valid api_base
        if not api_base:
            error_msg = 'No valid API base URL configured. Please configure an LLM model in "LLM 模型管理" with a valid API Base (e.g., http://127.0.0.1:11434/v1 for Ollama).'
            logger.error(f" {error_msg}")
            return error_response(error_msg, 400)

        from app.models.image import Image, ImageType
        from conf import UPLOAD_FOLDER, OUTPUT_FOLDER
        import base64
        import requests
        
        def encode_image_to_base64(file_path: str) -> str:
            try:
                with open(file_path, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                logger.error(f"Failed to encode image {file_path}: {e}")
                return ""

        def fetch_images_in_order(id_list):
            if not id_list:
                return []
            records = Image.query.filter(Image.id.in_(id_list)).all()
            record_map = {img.id: img for img in records}
            ordered = []
            for image_id in id_list:
                img = record_map.get(image_id)
                if img:
                    ordered.append(img)
            return ordered

        selected = []
        seen_ids = set()

        for group_ids in (rule_ids, regular_ids, event_ids):
            for img in fetch_images_in_order(group_ids):
                if img.id not in seen_ids:
                    selected.append(img)
                    seen_ids.add(img.id)

        # Encode images
        image_base64_list = []
        image_formats = []  # Track formats for each image
        
        for img in selected:
            file_path = img.file_path
            full_path = None

            if file_path.startswith('/uploads/'):
                filename = file_path.replace('/uploads/', '')
                full_path = os.path.join(UPLOAD_FOLDER, filename)
            elif file_path.startswith('/output/'):
                filename = file_path.replace('/output/', '')
                full_path = os.path.join(OUTPUT_FOLDER, filename)
            elif os.path.isabs(file_path):
                full_path = file_path
            else:
                full_path = os.path.join(UPLOAD_FOLDER, file_path)

            logger.info(f" Processing: {img.filename}")
            logger.info(f"   DB path: {img.file_path}")
            logger.info(f"   Full path: {full_path}")
            logger.info(f"   Exists: {os.path.exists(full_path)}")
            
            if os.path.exists(full_path):
                encoded = encode_image_to_base64(full_path)
                if encoded:
                    # Detect image format from filename
                    ext = os.path.splitext(full_path)[1].lower()
                    format_map = {
                        '.jpg': 'jpeg',
                        '.jpeg': 'jpeg',
                        '.png': 'png',
                        '.webp': 'webp',
                        '.gif': 'gif',
                        '.bmp': 'bmp'
                    }
                    img_format = format_map.get(ext, 'jpeg')  # Default to jpeg if unknown
                    
                    image_base64_list.append(encoded)
                    image_formats.append(img_format)
                    logger.info(f" Encoded: {img.filename} ({len(encoded)} bytes, format: {img_format})")
            else:
                logger.error(f" Not found: {full_path}")
        
        logger.info(f" Total encoded: {len(image_base64_list)}/{len(selected)}")

        # Build prompt text
        prompt_parts = []
        if selected:
            prompt_parts.append(f"已选择 {len(selected)} 张图片")
        if payload.get('custom_prompt'):
            prompt_parts.append(f"\n{payload['custom_prompt']}")
        else:
            prompt_parts.append("\n请生成吸引人的广告文案")
        
        user_prompt_text = "\n".join(prompt_parts)

        # Use OpenAI-compatible API
        # Default: Prepare payload for Ollama's single-shot generation API (/api/generate)
        # This endpoint also supports multimodal inputs via the top-level "images" array
        # Reference: https://docs.ollama.com/api/generate
        ollama_base = api_base.replace('/v1', '').rstrip('/')
        ollama_url = f"{ollama_base}/api/generate"

        payload_data = {
            "model": model,
            "prompt": user_prompt_text,
            "stream": False,
        }
        if image_base64_list:
            payload_data["images"] = image_base64_list

        image_metadata = [
            {
                "id": getattr(img, "id", None),
                "filename": img.filename,
                "db_path": img.file_path,
                "resolved_path": (
                    os.path.join(UPLOAD_FOLDER, img.file_path.replace('/uploads/', ''))
                    if img.file_path.startswith('/uploads/')
                    else (
                        os.path.join(OUTPUT_FOLDER, img.file_path.replace('/output/', ''))
                        if img.file_path.startswith('/output/')
                        else img.file_path
                    )
                ),
                "base64_length": len(image_base64_list[idx]) if idx < len(image_base64_list) else 0,
            }
            for idx, img in enumerate(selected)
        ]

        request_snapshot = {
            "type": "ollama_generate_request",
            "url": ollama_url,
            "model": model,
            "image_count": len(image_base64_list),
            "images": image_metadata,
            "prompt": user_prompt_text,
            "payload": payload_data,
        }

        logger.info(
            "[OLLAMA REQUEST] %s",
            json.dumps(request_snapshot, ensure_ascii=False),
        )
        
        # First, check if Ollama is accessible and the model exists
        try:
            ollama_tags_url = f"{ollama_base}/api/tags"
            tags_response = requests.get(ollama_tags_url, timeout=5)
            if tags_response.ok:
                available_models = [m.get('name', '') for m in tags_response.json().get('models', [])]
                logger.info(f" Available Ollama models: {available_models}")
                
                # Check if our model is available (handle model:tag format)
                model_base = model.split(':')[0] if ':' in model else model
                model_found = any(model_base in m for m in available_models)
                if not model_found:
                    error_msg = f"Model '{model}' not found in Ollama. Available models: {available_models}. Please run: ollama pull {model}"
                    logger.error(f" {error_msg}")
                    return error_response(error_msg, 400)
            else:
                logger.warning(f" Could not check Ollama models: {tags_response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f" Could not connect to Ollama for model check: {e}")
        
        response = requests.post(ollama_url, json=payload_data, timeout=120)
        
        # Better error handling for non-200 responses
        if not response.ok:
            error_detail = ""
            try:
                error_json = response.json()
                error_detail = error_json.get('error', str(error_json))
            except:
                error_detail = response.text[:500] if response.text else f"HTTP {response.status_code}"
            
            logger.error(f" Ollama returned {response.status_code}: {error_detail}")
            
            # Provide helpful error messages
            if response.status_code == 502:
                error_msg = f"Ollama 502 Bad Gateway. This usually means: 1) Model '{model}' is not pulled (run: ollama pull {model}), 2) Model is still loading, or 3) Out of memory. Details: {error_detail}"
            elif response.status_code == 404:
                error_msg = f"Model '{model}' not found. Run: ollama pull {model}"
            else:
                error_msg = f"Ollama error {response.status_code}: {error_detail}"
            
            return error_response(error_msg, response.status_code)
        
        result = response.json()
        
        logger.info(" RECEIVED RESPONSE FROM OLLAMA /api/generate")
        logger.info(json.dumps(result, indent=2, ensure_ascii=False))
        logger.info("=" * 80)
        
        content = result.get('response', '').strip()
        if not content:
            raise ValueError("No content in Ollama response")
        
        return success_response({"prompt": content})
    except requests.exceptions.ConnectionError as e:
        logger.error(f" Cannot connect to Ollama at {ollama_url}")
        logger.exception('Connection error:')
        return error_response(f'Cannot connect to Ollama. Make sure Ollama is running: ollama serve', 503)
    except requests.exceptions.Timeout as e:
        logger.error(f" Ollama request timed out after 120s")
        return error_response('Ollama request timed out. The model may be loading or the request is too large.', 504)
    except Exception as e:
        logger.error(" ERROR")
        logger.exception('Error details:')
        return error_response(f'Failed to generate participation prompt: {str(e)}', 500)