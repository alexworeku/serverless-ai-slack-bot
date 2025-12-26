from abc import ABC, abstractmethod
import json
import logging
from typing import List, Optional
from botocore.exceptions import ClientError
from src.models.slack_message_model import SlackMessageModel

logger = logging.getLogger(__name__)
class MessageQueueService(ABC):
    @abstractmethod
    def send(self, message: SlackMessageModel)->bool:
        pass
    
    @abstractmethod
    def receive(self, max_message_num:int, visibility_timeout_sec:Optional[int]=0, wait_time_sec:Optional[int]=0)->List[SlackMessageModel]:
        pass
    @abstractmethod
    def delete_messages(self, receipt_handles:List[str])->bool:
        pass
    
class SQSMessageQueue(MessageQueueService):
    def __init__(self, queue):
        self.queue = queue
        super().__init__()
    
    def send(self, message: SlackMessageModel)->bool:
        try:
            response =  self.queue.send_message(
                MessageBody = message.model_dump_json())
            logger.info("Message sent to queue. MessageId: %s",response['MessageId'])
            return True
        except ClientError as e:
            logger.exception("Send message failed: %s",e)
            return False
        
    def receive(self, max_message_num:int, visibility_timeout_sec:Optional[int]=0, wait_time_sec:Optional[int]=0)->List[SlackMessageModel]:
        try:
            response = self.queue.receive_messages(
                MaxNumberOfMessages = max_message_num,
                WaitTimeSeconds = wait_time_sec,
                VisibilityTimeout = visibility_timeout_sec
            )
            
            messages = []
            print(response)
            for Ind, message in enumerate(response):
                slack_message = SlackMessageModel(**(json.loads(message.body)))
                slack_message.sqs_receipt_handle = message.receipt_handle
                
                messages.append(slack_message)
            
            return messages        
        except ClientError as e:
            logger.exception("Receive message failed: %s",e)
            return []
    def delete_messages(self, receipt_handles: List[str])->bool:
        
        try:
            entries = [{"Id": str(idx), 'ReceiptHandle':receipt_handle} for idx, receipt_handle in enumerate(receipt_handles)]
            
            response = self.queue.delete_messages(Entries = entries)
            if 'Failed' in response:
                for failure in response['Failed']:
                    # Log the specific ID that failed so you can investigate
                    logger.error(f"Failed to delete batch ID {failure['Id']}: {failure['Message']}")
                return False
            else:
                return True
        except ClientError as e:
            logger.exception("Couldn't delete messages: %s",e)  
            return False
        