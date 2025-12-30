from pydantic import BaseModel

class ProjectChannel(BaseModel):
    channel_id:str
    project_id:str