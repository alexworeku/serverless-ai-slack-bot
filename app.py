import os
import logging
import sys
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


from listeners import register_listeners 
from utilities import get_missing_env_vars, query_createai 


def main():
    logging.basicConfig(level=logging.INFO)

    load_dotenv()

    REQUIRED_ENV_VARS = [
        "SLACK_BOT_TOKEN", 
        "SLACK_APP_TOKEN", 
        
        "CREATEAI_PROJECT_ID",
        "CREATEAI_API_URL",
        "CREATEAI_TOKEN"
    ]

    missing_vars = get_missing_env_vars(REQUIRED_ENV_VARS)

    if missing_vars:
        logger.critical(
            f"CRITICAL ERROR: Missing environment variables: {', '.join(missing_vars)}"
        )
        sys.exit(1)
        
    app = App(token=os.environ["SLACK_BOT_TOKEN"])
    register_listeners(app)
    
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
    

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("Starting Slack Bot in Socket Mode...")
    main()
