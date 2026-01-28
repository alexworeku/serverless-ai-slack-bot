from pydantic import BaseModel

class ProjectChannelModel(BaseModel):
    channel_id:str
    project_id:str