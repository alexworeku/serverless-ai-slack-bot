import logging
from utilities import query_createai 

logger = logging.getLogger(__name__)

def register_listeners(app):
    app.event("app_mention")(handle_all_messages)
    app.message()(handle_all_messages)
    logger.info("All Slack listeners registered.")

def handle_all_messages(message, say, logger, context):
    
    if message.get("subtype") == "bot_message":
        logger.debug(f"Ignoring message from other bot: {message.get('bot_id')}")
        return

    user_id = message.get("user")
    user_message = message.get("text") 
    
    if not user_message:
        return
    
    user_message = user_message.replace(f'<@{context.get("bot_user_id")}>', '').strip()
    
    llm_response = query_createai(user_message)

    if llm_response:
        say(text=llm_response, thread_ts=message.get('ts'))