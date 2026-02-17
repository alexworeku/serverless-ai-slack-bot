# AI Slack Connector

A serverless Slack bot connector that integrates with LLM API to provide intelligent responses to Slack messages. Built with AWS SAM (Serverless Application Model) using Python 3.11 and deployed on AWS Lambda.

## Architecture

This application uses a serverless architecture with the following components:

### AWS Resources
- **API Gateway**: HTTP endpoint for Slack webhook events
- **Lambda Functions**: 
  - `SlackMessageListenerFunction`: Receives and validates Slack events
  - `SlackMessageProcessorFunction`: Processes messages and queries AI
- **SQS Queue**: Message queue for asynchronous processing
- **DynamoDB Tables**: 
  - `Projects`: Stores project configurations and API credentials
  - `ProjectChannel`: Maps Slack channels to projects

### Function Flow
1. Slack sends webhook events to the API Gateway endpoint
2. `SlackMessageListenerFunction` validates the request and forwards messages to SQS
3. `SlackMessageProcessorFunction` consumes messages from SQS, queries the LLM API, and responds in Slack

## Features

- **Slack Integration**: Receives and responds to Slack messages in real-time
- **AI-Powered Responses**: Integrates with LLM API for intelligent responses
- **Project Management**: Supports multiple projects with channel-based routing
- **Secure Authentication**: Slack signature verification and secure credential storage
- **Asynchronous Processing**: Uses SQS for reliable message processing
- **Serverless**: Cost-effective and scalable architecture

## Prerequisites

- AWS CLI configured with appropriate permissions
- SAM CLI installed
- Python 3.11
- Slack App with:
  - Bot token (`xoxb-...`)
  - Signing secret
  - Events API subscription for `message.channels`

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd serverless-ai-slack-bot
   ```

2. **Set up Python virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r layers/requirements.txt
   ```

## Configuration

### Environment Variables
The following parameters are required during deployment:

- `SlackSigningSecret`: Your Slack app's signing secret
- `SlackBotToken`: Your Slack bot token (starts with `xoxb-`)
- `ProjectChannelIndexName`: DynamoDB GSI name (default: "ProjectChannelIndex")

### Slack App Setup
1. Create a Slack app at https://api.slack.com/apps
2. Enable Bot Token Scopes:
   - `chat:write`
   - `channels:history`
   - `channels:read`
3. Set up Event Subscriptions:
   - Request URL: `https://<your-api-gateway-url>/slack-event`
   - Subscribe to: `message.channels`
4. Install the app to your workspace

## Deployment

1. **Build the application**
   ```bash
   sam build
   ```

2. **Deploy to AWS**
   ```bash
   sam deploy --guided
   ```
   
   Follow the prompts to provide the required parameters.

3. **Update Slack Webhook URL**
   After deployment, copy the API Gateway URL from the stack outputs and update your Slack app's Event Subscription URL.

## Project Management

### Adding Projects
Projects are stored in the `Projects` DynamoDB table with the following structure:

```python
{
    "project_id": "string",
    "api_token": "string", 
    "api_url": "string",
    "project_owner_email": "string",
    "created_at": "datetime",
    "updated_at": "datetime", 
    "status": "ACTIVE|INACTIVE"
}
```

### Channel Mapping
Map Slack channels to projects in the `ProjectChannel` table:

```python
{
    "channel_id": "string",
    "project_id": "string"
}
```

## Local Development

### Testing Functions
```bash
# Test message listener
sam local invoke SlackMessageListenerFunction -e events/slack-event.json

# Test message processor  
sam local invoke SlackMessageProcessorFunction -e events/sqs-event.json
```

### Logging
- All functions use JSON structured logging
- Logs are available in CloudWatch
- Local logging level is set to INFO

## Security Considerations

- Slack signatures are verified (currently commented out for testing)
- API credentials should be encrypted at rest in DynamoDB
- Lambda functions use least-privilege IAM roles
- Environment variables contain sensitive data and are marked as `NoEcho`

## Monitoring

- **CloudWatch Logs**: All function logs and errors
- **SQS Metrics**: Queue depth and processing metrics  
- **DynamoDB Metrics**: Read/write capacity and throttling
- **Lambda Metrics**: Invocations, duration, and error rates

## Troubleshooting

### Common Issues

1. **Invalid Slack Signature**: Ensure the signing secret is correctly set
2. **SQS Timeouts**: Check the visibility timeout (70s) matches Lambda timeout
3. **DynamoDB Permissions**: Verify IAM policies allow table access
4. **Slack Bot Permissions**: Ensure bot is added to target channels

### Debugging

Enable debug logging by modifying the logging level in the Lambda functions:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Cost Optimization

- DynamoDB uses pay-per-request billing
- Lambda functions have reasonable timeout settings (10s for listener, 60s for processor)
- SQS message retention is set to 1 day
- ARM64 architecture for better price-performance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with `sam local invoke`
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check CloudWatch logs for error details
- Verify Slack app configuration
- Ensure AWS IAM permissions are correctly set
