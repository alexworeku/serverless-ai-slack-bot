from abc import ABC, abstractmethod
import logging
from typing import List
from models.project_channel_model import ProjectChannel
from models.project_model import ProjectModel
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
class ProjectRepository(ABC):
    @abstractmethod
    def upsert(self,channel_id:str, project: ProjectModel)->bool:
        pass
    @abstractmethod
    def get_by_owner(self, owner_email:str)->List[ProjectModel]:
        pass
    @abstractmethod
    def get_projects_by_channel(self, channel_id:str)->List[ProjectModel]:
        pass
    
    @abstractmethod
    def get_channels_by_project(self, project_id:str)->List[ProjectChannel]:
        pass
    
    @abstractmethod
    def delete_project(self, project_id:str)->bool:
        pass
    @abstractmethod
    def unlink_projects_from_channels(self, project_channels:List[ProjectChannel])->bool:
        pass
    @abstractmethod
    def link_project_to_channels(self, project_channels:List[ProjectChannel])->bool:
        pass
    @abstractmethod
    def get_all_projects(self,last_evaluated_key:dict=None)->tuple[List[ProjectModel], str]:
        pass
    
logger = logging.getLogger(__name__)

class DynamoProjectRepository(ProjectRepository):
    def __init__(self, dyn_resource, projects_table_name,project_channel_table_name,proj_ch_index_name):
        self.dyn_resource = dyn_resource
        self.projects_table_name = projects_table_name
        self.project_channel_table_name = project_channel_table_name
        self.proj_ch_index_name= proj_ch_index_name
        
        self.projects_table = dyn_resource.Table(projects_table_name)
        self.project_channel_table = dyn_resource.Table(project_channel_table_name)
        
        super().__init__()
    
    def upsert(self,channel_id:str, project: ProjectModel)->bool:
        try:
            self.projects_table.put_item(Item = project.model_dump(mode='json'))
            project_channel = ProjectChannel(channel_id=channel_id,project_id=project.project_id)
            self.project_channel_table.put_item(Item=project_channel.model_dump(mode='json'))
            
            return True
        except ClientError as e:
            logger.error("Couldn't add a record to table %s, because of %s:%s", 
                         self.projects_table_name, 
                         e.response['Error']['Code'], 
                         e.response['Error']['Message'])
            return False
            
   
    def get_by_owner(self, owner_email:str)->List[ProjectModel]:
       pass


    def get_projects_by_channel(self, channel_id:str)->List[ProjectModel]:
        try:

            response = self.project_channel_table.query(
                KeyConditionExpression=Key('channel_id').eq(channel_id)
            )
            
            items = response.get('Items', [])
            logger.info(f"Found {len(items)} project mappings for channel {channel_id}")

      
            project_keys = [{"project_id": item['project_id']} for item in items]

         
            if not project_keys:
                return []

          
            result = self.dyn_resource.batch_get_item(
                RequestItems={
                    self.projects_table_name: {
                        "Keys": project_keys
                    }
                }
            )

    
            if result.get("UnprocessedKeys", {}):
                logger.warning(f"Unprocessed keys remaining: {result['UnprocessedKeys']}")


            raw_projects = result.get("Responses", {}).get(self.projects_table_name, [])
            
            return [ProjectModel(**p) for p in raw_projects]

        except ClientError as e:
            logger.error(f"DynamoDB Error: {e.response['Error']['Message']}")
            return []
        
    def get_channels_by_project(self, project_id:str)->List[ProjectChannel]:
        
        try:
            result = self.project_channel_table.query(
                IndexName = self.proj_ch_index_name,
                KeyConditionExpression = Key('project_id').eq(project_id))
           
            proj_channels = []
            if result.get("Items"):
                
                proj_channels = [ProjectChannel(**item) for item in result.get("Items")]
                
                return proj_channels

        except ClientError as e:
            logger.error("Couldn't get records from %s, because of %s:%s", 
                        self.project_channel_table_name, 
                        e.response['Error']['Code'], 
                        e.response['Error']['Message'])
        
        
    def delete_project(self, project_id:str)->bool:
        try:
            self.projects_table.delete_item(
                Key={
                    'project_id':project_id
                }
            )
            return True
        except ClientError  as e:
            logger.error("Couldn't delete the records from %s, because of %s:%s", 
                        self.projects_table_name, 
                        e.response['Error']['Code'], 
                        e.response['Error']['Message'])
            return False
        
    def unlink_projects_from_channels(self, project_channels:List[ProjectChannel])->bool:
        
        try:
        
            with self.project_channel_table.batch_writer() as batch:
                for proj_ch in project_channels:
                    batch.delete_item(
                        Key =  {
                                "project_id": proj_ch.project_id,
                                "channel_id":proj_ch.channel_id
                                } 
                    )
            return True
        except ClientError as e:
            logger.error(
                "Couldn't delete records from %s: %s:%s",
                self.project_channel_table_name,
                e.response['Error']['Code'],
                e.response['Error']['Message']
            )
            return False
            
    def link_project_to_channels(self, project_channels:List[ProjectChannel])->bool:
        try:
            
            with self.project_channel_table.batch_writer() as batch:
                for proj_ch in project_channels:
                    batch.put_item(
                    Item = proj_ch.model_dump(mode='json'))
            
            
            return True
        except ClientError as e:
            logger.error("Couldn't add records to table %s, because of %s:%s", 
                            self.projects_table_name, 
                            e.response['Error']['Code'], 
                            e.response['Error']['Message'])
            return False

    
    def get_all_projects(self, last_evaluated_key:dict=None)->tuple[List[ProjectModel], str]:
        try:
            response = {}
            if last_evaluated_key:
                response = self.projects_table.scan(ExclusiveStartKey=last_evaluated_key)
            else:
                response = self.projects_table.scan()
            
            projects=[ProjectModel(**item) for item in response.get('Items',[])]
            
            return (projects,response.get("LastEvaluatedKey",""))
            
        except ClientError  as e:
            logger.error("Couldn't get records from %s, because of %s:%s", 
                        self.projects_table_name, 
                        e.response['Error']['Code'], 
                        e.response['Error']['Message'])
            return ()
        