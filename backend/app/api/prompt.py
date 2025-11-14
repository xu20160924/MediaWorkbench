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