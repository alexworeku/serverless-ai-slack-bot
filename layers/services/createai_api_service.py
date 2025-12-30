import logging
import time
from typing import Optional

import requests

logger = logging.getLogger(__name__)

class CreateAIAPIService:
    def __init__(self):
        pass
    def query(self, url:str,token:str, proj_id:str, q:str, session_id:Optional[str]=None):
        payload = {
        'action': 'query',
        'query': q,
        'session_id': session_id if session_id else f'slack-{int(time.time() * 1000)}',
        'project_id':proj_id,
        'model_params': {
            'enable_search': True,
            'search_params':{
                'collection': proj_id
            }
        }
       }
        headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
        }
        try:
            response = requests.post(
                url=url,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"Request failed: {e}")
            # Optional: access detailed error info if raise_for_status was the cause
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status Code: {e.response.status_code}")
            raise