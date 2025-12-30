import json
import logging
import os

import boto3

from services.createai_api_service import CreateAIAPIService
from infrastructure.project_repo import DynamoProjectRepository
from models.project_model import ProjectModel
from services.slack_service import SlackService

os.environ['TRANSFORMERS_CACHE'] = '/tmp'
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/tmp'


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



PROJ_TABLE_NAME = os.environ.get('PROJ_TABLE_NAME','Projects')
PROJCHANNEL_TABLE_NAME = os.environ.get('PROJCHANNEL_TABLE_NAME','ProjectChannel')
PROJCHANNEL_GSI_NAME = os.environ.get('PROJCHANNEL_GSI_NAME','ProjectChannelIndex')
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

dynamodb  = boto3.resource('dynamodb')
project_repo = DynamoProjectRepository(dynamodb, PROJ_TABLE_NAME, PROJCHANNEL_TABLE_NAME, PROJCHANNEL_GSI_NAME)
slack_service = SlackService(SLACK_BOT_TOKEN)
createAI_API = CreateAIAPIService()

# TODO: Load Encryption/Decryption Keys
def decrypt_credentials(proj:ProjectModel):
    # TODO: Decrypt Credentials
    return proj
def process_messages(data,context):
    for record in data['Records']:
        try:
          
          
            record_dict=json.loads(record['body'])
            if not record_dict.get('text'):
                continue
            
            # Get API Credentials
            projects = project_repo.get_projects_by_channel(channel_id=record_dict.get('channel'))
           
            logging.info(f"{len(projects)} Projects Loaded")
            
            if projects:

                project = decrypt_credentials(projects[0])
                
                llm_response = createAI_API.query(project.api_url, project.api_token, project.project_id, record_dict.get('text'))
                
                if llm_response.status_code != 200:
                    logger.error(f"LLM API Error: {llm_response.status_code} - {llm_response.text}")
                    continue
            
                llm_response = llm_response.json()
                response_text = llm_response.get('response')

                if response_text: 
                    slack_response = slack_service.reply_to_thread(
                        record_dict.get('channel'),
                        record_dict.get('ts'),
                        response_text
                    )
                    logger.info(f'Slack Reply Response {slack_response}')
        except Exception as e:
            logger.error("Failed to process message: %s",e)
            # raise e
        
    return {"statusCode": 200}