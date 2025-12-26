from datetime import datetime, timezone
import logging
import boto3
from src.models.project_channel_model import ProjectChannel
from src.models.project_model import ProjectModel, ProjectStatus
from src.infrastructure.project_repo import DynamoProjectRepository
logging.basicConfig(
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def test_dynamodb_repo():
    
    try:
        
        dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
        project_repo=DynamoProjectRepository(
            dyn_resource=dynamodb, 
            projects_table_name="Projects", 
            project_channel_table_name="ProjectChannel",
            proj_ch_index_name="ProjectChannelsIndex"
            )

        # test_proj = ProjectModel(
        #     project_id="proj123",
        #     api_token="andjskdjkansjdasnk8asdd",
        #     api_url="https://api-dev-poc.aiml.asu.edu/query",
        #     project_owner_email="aababu@asu.edu",
        #     created_at=datetime.now(timezone.utc).isoformat(),
        #     updated_at=datetime.now(timezone.utc).isoformat(),
        #     status=ProjectStatus.ACTIVE
        #     )
        
        # result = project_repo.upsert(channel_id="dasjdkna3sas", project=test_proj)
        # logger.info("Project added: %s", result)

        # projects,last_key = project_repo.get_all_projects()
        # logger.info("Loaded Projects from DDB: %s \n last key: %s", len(projects), last_key)
        
        
        # projects = project_repo.get_all_by_channel(channel_id="dasjdkna3sas")
        # logger.info("Projects in a channel: %s", projects)
        
        result = project_repo.unlink_projects_from_channels(
           project_channels=[
               ProjectChannel(
                   channel_id="dasjdkna3sas",
                   project_id="proj123"
               )
           ]
        )
        logger.info("Project unlinked: %s",result)
        
        # result= project_repo.link_project_to_channels(
        #         [
        #             ProjectChannel(   
        #                 channel_id="dasjdkna3sas",
        #                 project_id="proj123"
        #                 )
        #         ])
        # logger.info("Project linked: %s",result)
        
        # proj_channels = project_repo.get_channels_by_project(project_id="proj123")
        # logger.info("Channels Count: %s", proj_channels)
        
        # result = project_repo.delete_project(project_id="proj123")
        # logger.info("Project deleted: %s", result)
        
    except Exception as e:
        logger.exception(e)


if __name__ =="__main__":
    test_dynamodb_repo()