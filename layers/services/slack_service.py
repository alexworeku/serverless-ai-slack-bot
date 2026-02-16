import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackService:
    def __init__(self,slack_bot_token):
        self.client = WebClient(token=slack_bot_token)

    def reply_to_thread(self, channel_id, thread_ts, text):
        try:
            response = self.client.chat_postMessage(
                channel=channel_id,
                thread_ts=str(thread_ts), 
                text=text
            )
            return response
        except SlackApiError as e:
            error_code = e.response['error']
            print(f"!!! SLACK API ERROR: {error_code} !!!")
            
            if error_code == 'not_in_channel':
                print("-> Fix: Type /invite @YourBotName in the channel")
            elif error_code == 'missing_scope':
                print("-> Fix: Reinstall the app in the Slack Dashboard")
            elif error_code == 'invalid_auth':
                print("-> Fix: Your token is wrong or expired")
                
            return None