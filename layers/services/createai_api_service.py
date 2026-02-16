import logging
import time
from typing import Optional
import re
import requests
import json
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
            data=parse_strict_markdown_json(response.json())
            logger.info(f"LLM Response Parsed(/query):\n {data}")
            return data
        except Exception as e:
            logger.error(f"Request failed: {e}")
            # Optional: access detailed error info if raise_for_status was the cause
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status Code: {e.response.status_code}")
            raise
    def get_decorated_prompt(self, message_text:str)->str:
        return f"""
                You are an assistant that answers questions from Slack messages.
                Your task:
                - Answer the Slack message clearly and concisely.
                - If you cannot provide a clear and confident answer, or if the response would  include uncertainty or refusal (for example: "I don't know", "I'm not sure",  "I can't answer this", or similar), then set answered to false.
                - If you provide a meaningful, direct answer, set answered to true.
                
                Output rules:
                - Respond ONLY with valid JSON.
                - Do not include any extra text.
                - Follow this exact schema:{{  "answer": string,  "answered": boolean}}
                
                --- SLACK MESSAGE START ---
                {message_text}
                
                --- SLACK MESSAGE END ---

             """
def parse_strict_markdown_json(response_dict):
    raw_content = response_dict.get('response', '')
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    
    match = re.search(pattern, raw_content, re.DOTALL)

    if not match:
        logger.error("❌ Parser Error: No markdown code block found.")
        return None  # Or raise ValueError("Response not in markdown format")

    json_str = match.group(1)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON Error: Content inside markdown is not valid JSON. {e}")
        return None