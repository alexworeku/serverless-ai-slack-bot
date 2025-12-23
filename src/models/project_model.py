import datetime
from enum import  StrEnum,auto
from pydantic import BaseModel

class ProjectModel(BaseModel):
    project_id:str
    api_token:str
    api_url:str
    project_owner_email:str
    created_at:datetime
    updated_at:datetime
    status:ProjectStatus
    channel_id:str
    
class ProjectStatus(StrEnum):
    ACTIVE = auto()
    INACTIVE = auto()