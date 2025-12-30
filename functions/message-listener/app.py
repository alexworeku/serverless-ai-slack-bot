import json
import logging
import os
import time
import hmac
import hashlib
import base64

import boto3


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO
)

sqs = boto3.client('sqs')
QUEUE_URL = os.environ.get('QUEUE_URL','')
events_to_handle = ['message']


def verify_slack_signature(event):
    signing_secret = os.environ.get('SLACK_SIGNING_SECRET')
    if not signing_secret:
        return False

    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    slack_signature = headers.get('x-slack-signature')
    slack_timestamp = headers.get('x-slack-request-timestamp')

    if not slack_signature or not slack_timestamp:
        return False


    if abs(time.time() - int(slack_timestamp)) > 60 * 5:
        return False

    body = event.get('body', '')
    if event.get('isBase64Encoded'):
        body = base64.b64decode(body).decode('utf-8')

    # Formula: v0 + HMAC_SHA256(Secret, "v0:timestamp:body")
    base_string = f"v0:{slack_timestamp}:{body}".encode('utf-8')
    computed_signature = 'v0=' + hmac.new(
        signing_secret.encode('utf-8'),
        base_string,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_signature, slack_signature)

def handle_slack_message(event,context):
    
    # if not verify_slack_signature(event):
    #     logger.warning('Invalid signature! Rejecting request.')
    #     return {'statusCode': 401, 'body': 'Invalid signature'}
    
    body = json.loads(event.get('body', '{}'))
    slack_event = body.get('event', {})
    if slack_event.get('type') == 'url_verification':
       return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            "challenge": body.get('challenge')
        })
       }
    logger.info(f"Received Slack Event: {body}")
   
    if slack_event.get('bot_id') is not None or slack_event.get('subtype') == 'bot_message':
        logger.info(f"Skipping bot message: {slack_event.get('bot_id')}")
        return {'statusCode': 200, 'body': 'Ignored bot message'}
     
    if  slack_event.get('type') in events_to_handle:
        
        slack_message = {
                "user":slack_event.get('user'),
                "text":slack_event.get('text'),
                "ts":slack_event.get('ts'),
                "channel":slack_event.get('channel')
            }
    
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(slack_message) )
        logger.info(f'Sent message to SQS: {json.dumps(slack_message)}')

    return {'statusCode': 200, 'body': 'OK'}


    
