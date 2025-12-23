from abc import ABC, abstractmethod
import logging
from typing import List, Optional
from src.models.project_model import ProjectModel
import boto3
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
    def get_all_by_channel(self, channel_id:str)->List[ProjectModel]:
        pass
    @abstractmethod
    def delete(self, channel_id:str, project_id:str)->bool:
        pass
    @abstractmethod
    def get_all(self)->tuple[List[ProjectModel], str]:
        pass
    
logger = logging.get_logger(__name__)

class DynamoProjectRepository(ProjectRepository):
    def __init__(self, dyn_resource, table_name):
        self.table_name = table_name
        self.table = dyn_resource.Table(table_name)
    
    def upsert(self,project: ProjectModel)->bool:
        try:
            self.table.put_item(Item = project.model_dump(mode='json'))
            return True
        except ClientError as e:
            logger.error("Couldn't add a project to table %s, because of %s:%s", 
                         self.table_name, 
                         e.response['Error']['Code'], 
                         e.response['Error']['Message'])
            raise
            
   
    def get_by_owner(self, owner_email:str)->List[ProjectModel]:
       pass


    def get_all_by_channel(self, channel_id:str)->List[ProjectModel]:
        try:
            response = self.table.query(
                KeyConditionExpression = Key('channel_id').eq(channel_id)
            )
            projects=[ProjectModel(**item) for item in response.get('Items',[])]
            return projects
            
        except ClientError  as e:
            logger.error("Couldn't get projects from %s, because of %s:%s", 
                        self.table_name, 
                        e.response['Error']['Code'], 
                        e.response['Error']['Message'])

    def delete(self, channel_id:str, project_id:str)->bool:
        try:
            self.table.delete_item(
                Key={
                    'channel_id':channel_id,
                    'project_id':project_id
                }
            )
            return True
        except ClientError  as e:
            logger.error("Couldn't delete the project from %s, because of %s:%s", 
                        self.table_name, 
                        e.response['Error']['Code'], 
                        e.response['Error']['Message'])
        
 
    def get_all(self, last_evaluated_key)->tuple[List[ProjectModel], str]:
        try:
            response = {}
            if last_evaluated_key:
                response = self.table.scan(ExclusiveStartKey=last_evaluated_key)
            else:
                response = self.table.scan()
                
            projects=[ProjectModel(**item) for item in response.get('Items',[])]
            
            return (projects,response['LastEvaluatedKey'])
            
        except ClientError  as e:
            logger.error("Couldn't get projects from %s, because of %s:%s", 
                        self.table_name, 
                        e.response['Error']['Code'], 
                        e.response['Error']['Message'])
        