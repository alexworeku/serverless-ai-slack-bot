import json
import os
import time
from typing import Any, Dict, List, Optional, Union
import logging

import requests

logger = logging.getLogger(__name__)


def check_required_env_vars(required_vars: List[str]) -> Optional[List[str]]:

    missing_vars = []
    for var in required_vars:
        if os.getenv(var) is None or os.getenv(var) == "":
            missing_vars.append(var)
    
    return missing_vars if missing_vars else None

def query_createai(query: str,session_id: Optional[str] = None) -> str | None:
    CREATEAI_API_URL = os.getenv('CREATEAI_API_URL', 'https://api-main-beta.aiml.asu.edu/query')
    CREATEAI_TOKEN = os.getenv('CREATEAI_TOKEN')
    CREATEAI_PROJECT_ID = os.getenv('CREATEAI_PROJECT_ID')
    MODEL_PROVIDER = os.getenv('MODEL_PROVIDER')
    MODEL_NAME = os.getenv('MODEL_NAME')
    
    if not CREATEAI_TOKEN:
        raise ValueError('CREATEAI_TOKEN is not set in environment variables')
    
    payload = {
        'action': 'query',
        'query': query,
        'session_id': session_id if session_id else f'slack-{int(time.time() * 1000)}'
    }
    if CREATEAI_PROJECT_ID:
        payload['project_id'] = CREATEAI_PROJECT_ID
        payload['model_params'] = {
            'enable_search': True,
            'search_params': {
                'collection': CREATEAI_PROJECT_ID
            }
        }
        print(f"✅ Using Project ID: {CREATEAI_PROJECT_ID}")
    else:
        print('⚠️  No Project ID set - using token\'s linked project')
        
    # Log the payload structure for debugging
    print('CreateAI Request:', {
        'url': CREATEAI_API_URL,
        'project_id': CREATEAI_PROJECT_ID if CREATEAI_PROJECT_ID else 'token-linked',
        'payload': json.dumps(payload, indent=2)
    })
    
    headers = {
        'Authorization': f'Bearer {CREATEAI_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            CREATEAI_API_URL, 
            json=payload, 
            headers=headers, 
            timeout=30
        )
        response.raise_for_status()

        try:
            response_data: Union[Dict[str, Any], str] = response.json()
        except json.JSONDecodeError:
            return response.text
        
        if isinstance(response_data, dict):
            response_text = response_data.get('response') or \
                            response_data.get('data', {}).get('response') or \
                            response_data.get('message')

            if response_text:
                return response_text
            else:
                return json.dumps(response_data, indent=2)
        
        elif isinstance(response_data, str):
            return response_data
        
        return f"Unexpected API response structure: {response_data}"

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code
        error_data = e.response.json() if e.response.content else {}
        
        error_msg = error_data.get('error') or \
                    error_data.get('message') or \
                    f"API Error: {status} {e.response.reason}"
        
        if status == 403:
            error_msg += ' (Check if your token is valid and has the correct permissions)'
        elif status == 401:
            error_msg += ' (Invalid or expired token)'
            
        print('CreateAI API Error:', {
            'status': status,
            'reason': e.response.reason,
            'data': error_data,
            'url': CREATEAI_API_URL
        })
        
        raise Exception(error_msg) from e
        
    except requests.exceptions.Timeout as e:
        raise Exception('No response from CreateAI API. Please check your network connection.') from e
        
    except requests.exceptions.RequestException as e:
        raise Exception(f'Request setup or network error: {e.__class__.__name__}') from e
    pass