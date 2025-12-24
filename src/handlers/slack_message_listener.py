import logging

from slack_bolt import App
from src.infrastructure.message_queue_service import MessageQueueService
from src.models.slack_message_model import SlackMessageModel

logger = logging.getLogger(__name__)


class SlackMessageListener:
    def __init__(self,app:App, mq_service:MessageQueueService):
        self.app = app
        self.mq_service = mq_service
        
        app.event("app_mention")(self.handle_all_messages)
        app.message()(self.handle_all_messages)
        logger.info("All Slack listeners registered.")
        

    def handle_messages(self,message, say, logger, context):
        try:
            # Fetch Message Details
            slack_message = SlackMessageModel(
                user_id= message.get('user'),
                user_message= message.get('text').replace(f'<@{context.get("bot_user_id")}>', '').strip(),
                channel_id=message.get('channel'),
                ts=message.get('ts')
            )
            # Push to Queue
            self.mq_service.send(slack_message)
        except Exception as e:
            logger.exception("Error handling slack event: %s", e)
        
        