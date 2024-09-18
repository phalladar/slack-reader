import os

import openai
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json
from datetime import datetime
import re

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

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

def display_messages(messages, indent=0):
    # Sort messages by timestamp, oldest first
    sorted_messages = sorted(messages, key=lambda x: float(x['ts']))
    
    for i, message in enumerate(sorted_messages):
        prefix = '│   ' * (indent - 1) + '├── ' if indent > 0 else ''
        if indent > 0 and i == len(sorted_messages) - 1:
            prefix = '│   ' * (indent - 1) + '└── '
        
        timestamp = format_timestamp(message['ts'])
        user = message.get('user', 'Unknown')
        text = message.get('text', '')
        
        if message.get('subtype') == 'channel_join':
            print(f"{prefix}{timestamp} - {text}")
        else:
            print(f"{prefix}{timestamp} - User {user}: {text}")

        if 'files' in message:
            for file in message['files']:
                print(f"{prefix}│   [File: {file['name']}]")

        if 'replies' in message:
            print(f"{prefix}│")
            display_messages(message['replies'], indent + 1)

def format_message_with_replies(message):
    # Start with the main message
    formatted_message = f"Message: {message['text']}\n"

    # If there are replies, add them to the formatted message
    if 'replies' in message:
        formatted_message += "Thread replies:\n"
        for reply in message['replies']:
            formatted_message += f"- {reply['text']}\n"

    return formatted_message

def categorize_message_with_replies(message):
    formatted_message = format_message_with_replies(message)

    prompt = f"""
    Here is a Slack message and its thread replies. Please categorize the conversation into one of these categories: 
    1. Urgent
    2. Informative
    3. Feedback
    4. Request for Action
    5. Social/Chit-chat
    6. Other

    Message and replies: {formatted_message}
    """

    response = openai.Completion.create(
        engine="gpt-4",
        prompt=prompt,
        max_tokens=150
    )
    return response['choices'][0]['text']

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
            message["category"] = categorize_message_with_replies(message)

        print(f"Retrieved {len(messages)} messages from channel {channel_url}")

        # Convert messages to JSON
        print("Channel content:")
        display_messages(json.dumps(messages, indent=2))

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

def main():
    # Simulate the event and context
    event = {}
    context = None

    result = lambda_handler(event, context)
    print(result)

if __name__ == "__main__":
    main()
