import logging
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime, timedelta
import re

SLACK_API_TOKEN = os.getenv("SLACK_API_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")
client = WebClient(token=SLACK_API_TOKEN)

def extract_channel_id(channel_url):
    match = re.search(r'/([A-Z0-9]+)$', channel_url)
    return match.group(1) if match else None

def _ensure_bot_in_channel(client, channel_id):
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
        return result["messages"][1:]
    except SlackApiError as e:
        print(f"Error fetching thread replies: {e}")
        return []

def _format_timestamp(ts):
    return datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')

def get_user_handle(client, user_id):
    try:
        result = client.users_info(user=user_id)
        return result["user"]["name"]
    except SlackApiError as e:
        print(f"Error fetching user info: {e}")
        return user_id

def get_channel_messages(channel_url, start_date, end_date):
    channel_id = extract_channel_id(channel_url)
    if not channel_id:
        logging.error("Invalid channel URL")
        return ""

    # Set default dates if not provided
    if not start_date:
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        logging.info(f"Start date not provided. Using default: {start_date}")

    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
        logging.info(f"End date not provided. Using default: {end_date}")

    try:
        start_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    except ValueError as e:
        logging.error(f"Error parsing dates: {e}")
        return ""

    try:
        _ensure_bot_in_channel(client, channel_id)

        logging.info(f"Fetching messages from {start_date} to {end_date}")
        result = client.conversations_history(
            channel=channel_id,
            oldest=start_timestamp,
            latest=end_timestamp
        )
        messages = result["messages"]

        while result['has_more']:
            logging.info("Fetching more messages...")
            result = client.conversations_history(
                channel=channel_id,
                oldest=start_timestamp,
                latest=end_timestamp,
                cursor=result['response_metadata']['next_cursor']
            )
            messages.extend(result["messages"])

        logging.info(f"Retrieved {len(messages)} messages")

        if not messages:
            logging.warning("No messages found in the specified date range")
            return ""

        # Fetch thread replies for messages with threads
        for message in messages:
            if "thread_ts" in message and message["thread_ts"] == message["ts"]:
                replies = get_thread_replies(client, channel_id, message["ts"])
                message["replies"] = replies

        formatted_messages = []
        for message in messages:
            timestamp = _format_timestamp(message['ts'])
            user_id = message.get('user', 'Unknown')
            user_handle = get_user_handle(client, user_id)
            text = message.get('text', '')

            formatted_message = f"{timestamp} - @{user_handle}: {text}"
            formatted_messages.append(formatted_message)

            if 'files' in message:
                for file in message['files']:
                    formatted_messages.append(f"[File: {file['name']}]")

            if 'replies' in message:
                for reply in message['replies']:
                    reply_timestamp = _format_timestamp(reply['ts'])
                    reply_user_id = reply.get('user', 'Unknown')
                    reply_user_handle = get_user_handle(client, reply_user_id)
                    reply_text = reply.get('text', '')
                    formatted_messages.append(f"  {reply_timestamp} - @{reply_user_handle}: {reply_text}")

        channel_content = "\n".join(formatted_messages)
        logging.info("Channel content retrieved successfully")
        logging.debug(f"Channel content:\n{channel_content}")
        return channel_content
    except SlackApiError as e:
        logging.error(f"Error fetching messages: {e}")
        return ""