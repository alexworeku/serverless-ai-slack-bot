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
                thread_ts=thread_ts, 
                text=text
            )
            return response
        except SlackApiError as e:
            print(f"Error posting to Slack: {e.response['error']}")
            return None