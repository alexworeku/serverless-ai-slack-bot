import logging
import boto3

from src.models.slack_message_model import SlackMessageModel
from src.infrastructure.message_queue_service import SQSMessageQueue
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO
)
QUEUE_NAME="MQ_Sparky"
def test_message_queue():
    try:
        sqs = boto3.resource(
                "sqs",
                endpoint_url='http://localhost:9324',
                region_name='us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test')
        queue = sqs.get_queue_by_name(QueueName = QUEUE_NAME)
        
        mq_service = SQSMessageQueue(queue=queue)

        # send_result = mq_service.send(SlackMessageModel(
        #     user_id="user123",
        #     user_message="user-message1",
        #     ts="2132321",
        #     channel_id="channel123",
        # ))
        
        # logger.info("Sent Message to Queue: %s", send_result)
        
        # result =  mq_service.receive(max_message_num=5)
        # logger.info("mq messages: %s",result)

# ee757cd5-34fd-4a8f-a5a2-d5d8b2b0f5f8#f6857176-496f-4816-9b65-703101564f73
# 44ac2c46-1064-4056-a733-5a48cd9141d5#605325a9-e482-498e-8758-5c37cfdb75ee

        delete_result = mq_service.delete_messages(['44ac2c46-1064-4056-a733-5a48cd9141d5#605325a9-e482-498e-8758-5c37cfdb75ee'])

            
        logger.info("Messages deleted: %s", delete_result)
    except Exception as e:
        logger.error(e)

def init_local_env():
        mq = boto3.resource(
            "sqs",
            endpoint_url='http://localhost:9324',
            region_name='us-east-1',
            aws_access_key_id='test',
            aws_secret_access_key='test')
        result = mq.create_queue(QueueName=QUEUE_NAME)
        return result
if __name__ == "__main__":
    # init_local_env()
    test_message_queue()