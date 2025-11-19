import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
load_dotenv()
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

@app.event("app_mention")
def handle_mention(body,say,logger):
    print(f"incoming event:\n {body}")
    # Extract Message
    event = body['event']
    message  = event['text']
    message_ts = event['ts']
    
    # @TODO Pass Message to CreateAI API
    # @TODO : Extract API Response & Reply on Slack
            # Identify Intent
            # Decide to either reply or loop in Human based on confidence score (returned from API)
            # Reply to Slack Message
            # DM Message Details to loopin a human (only if the LLM didn't know how to answer the question)
            # Include Link to the orginal conversation in the DM
    # Reply to Message
    say(
        text = f"Hey there <@{body['event']['user']}>!",
        thread_ts = message_ts)

    
if __name__ == "__main__":
    SocketModeHandler(app,os.environ['SLACK_APP_TOKEN']).start()


