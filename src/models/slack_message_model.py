from typing import Optional
from pydantic import BaseModel, Field


class SlackMessageModel(BaseModel):
    user_id: str
    user_message:str
    ts: str
    channel_id: str
    
    sqs_receipt_handle: Optional[str] = Field(default=None)
