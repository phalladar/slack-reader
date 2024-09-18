import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
from datetime import datetime
import re

load_dotenv()

def extract_channel_id(channel_url):
    match = re.search(r'/([A-Z0-9]+)$', channel_url)
    return match.group(1) if match else None

def ensure_bot_in_channel(client, channel_id):
    try:
        client.conversations_join(channel=channel_id)
        print(f"Bot joined the channel {channel_id}")
    except SlackApiError as e:
        if e.response["error"] == "already_in_channel":
            print(f"Bot is already in the channel {channel_id}")
        else:
            raise e

def get_thread_replies(client, channel_id, thread_ts):
    try:
        result = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )
        return result["messages"][1:]  # Exclude the parent message
    except SlackApiError as e:
        print(f"Error fetching thread replies: {e}")
        return []

def format_timestamp(ts):
    return datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')

def get_user_handle(client, user_id):
    try:
        result = client.users_info(user=user_id)
        return result["user"]["name"]
    except SlackApiError as e:
        print(f"Error fetching user info: {e}")
        return user_id

def display_messages(messages, indent=0, client=None):
    # Sort messages by timestamp, oldest first
    sorted_messages = sorted(messages, key=lambda x: float(x['ts']))
    
    for i, message in enumerate(sorted_messages):
        prefix = '│   ' * (indent - 1) + '├── ' if indent > 0 else ''
        if indent > 0 and i == len(sorted_messages) - 1:
            prefix = '│   ' * (indent - 1) + '└── '
        
        timestamp = format_timestamp(message['ts'])
        user_id = message.get('user', 'Unknown')
        user_handle = get_user_handle(client, user_id) if client else user_id
        text = message.get('text', '')
        
        if message.get('subtype') == 'channel_join':
            print(f"{prefix}{timestamp} - {text}")
        else:
            print(f"{prefix}{timestamp} - @{user_handle}: {text}")

        if 'files' in message:
            for file in message['files']:
                print(f"{prefix}│   [File: {file['name']}]")

        if 'replies' in message:
            print(f"{prefix}│")
            display_messages(message['replies'], indent + 1, client)

def main():
    # Simulate the event and context
    event = {}
    context = None
    
    result = lambda_handler(event, context)
    print(result)

def lambda_handler(event, context):
    # Initialize the Slack client
    slack_token = os.environ["SLACK_API_TOKEN"]
    client = WebClient(token=slack_token)

    # Get channel ID and date range from environment variables
    channel_url = os.environ["SLACK_CHANNEL"]
    channel_id = extract_channel_id(channel_url)
    if not channel_id:
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid channel URL')
        }

    start_date = os.environ["START_DATE"]
    end_date = os.environ["END_DATE"]

    # Convert dates to timestamps
    start_ts = datetime.strptime(start_date, "%Y-%m-%d").timestamp()
    end_ts = datetime.strptime(end_date, "%Y-%m-%d").timestamp()

    try:
        # Ensure bot is in the channel
        ensure_bot_in_channel(client, channel_id)

        # Fetch messages
        result = client.conversations_history(
            channel=channel_id,
            oldest=start_ts,
            latest=end_ts
        )

        # Process messages
        messages = result["messages"]
        
        # Fetch thread replies for messages with threads
        for message in messages:
            if "thread_ts" in message and message["thread_ts"] == message["ts"]:
                replies = get_thread_replies(client, channel_id, message["ts"])
                message["replies"] = replies

        print(f"Retrieved {len(messages)} messages")

        # Convert messages to JSON
        json_messages = json.dumps(messages, indent=2)
        print("Channel content:")
        display_messages(messages, client=client)

        return {
            'statusCode': 200,
            'body': json.dumps('Slack export completed successfully!')
        }

    except SlackApiError as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

if __name__ == "__main__":
    main()
