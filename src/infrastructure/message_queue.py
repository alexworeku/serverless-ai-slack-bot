from abc import ABC, abstractmethod
from typing import Optional

from src.models.slack_message_model import SlackMessageModel


class MessageQueue(ABC):
    @abstractmethod
    def send(message: SlackMessageModel)->bool:
        pass
    
    @abstractmethod
    def receive(max_message_num:int, visibility_timeout_sec:Optional[int]=0, wait_time_sec:Optional[int]=0)->Optional[SlackMessageModel]:
        pass
class SQS