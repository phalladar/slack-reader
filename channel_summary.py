import os
import logging
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
channel_id = os.environ["TARGET_CHANNEL_ID"]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_channel_messages(start_time, end_time):
    messages = []
    try:
        result = client.conversations_history(
            channel=channel_id,
            oldest=start_time,
            latest=end_time
        )
        messages.extend(result["messages"])
        while result["has_more"]:
            result = client.conversations_history(
                channel=channel_id,
                oldest=start_time,
                latest=end_time,
                cursor=result["response_metadata"]["next_cursor"]
            )
            messages.extend(result["messages"])
    except SlackApiError as e:
        print(f"Error fetching messages: {e}")
    return messages

def get_thread_replies(thread_ts):
    replies = []
    try:
        result = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )
        replies.extend(result["messages"][1:])  # Exclude the parent message
        while result["has_more"]:
            result = client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                cursor=result["response_metadata"]["next_cursor"]
            )
            replies.extend(result["messages"])
    except SlackApiError as e:
        print(f"Error fetching thread replies: {e}")
    return replies

def summarize_messages(messages):
    total_messages = len(messages)
    threaded_messages = sum(1 for msg in messages if "thread_ts" in msg)
    users = set(msg["user"] for msg in messages)

    formatted_messages = []
    for msg_id, msg_data in messages.items():
        formatted_msg = f"Message: {msg_data['text']}\n"
        if 'replies' in msg_data and msg_data['replies']:
            formatted_msg += "Replies:\n"
            for reply in msg_data['replies']:
                formatted_msg += f"- {reply['text']}\n"
    formatted_messages.append(formatted_msg)

    all_messages = "\n".join(formatted_messages)
    prompt = f"Please summarize the following messages posted in the #prouction-feedback Slack channel from the past week:\n\n{all_messages}\n\nSummary:"



    return summary

def post_summary(summary):
    try:
        client.chat_postMessage(
            channel=channel_id,
            text=summary
        )
    except SlackApiError as e:
        print(f"Error posting summary: {e}")

def run_weekly_summary():
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    messages = get_channel_messages(start_time.timestamp(), end_time.timestamp())

    for message in messages:
        if "thread_ts" in message:
            message["replies"] = get_thread_replies(message["thread_ts"])

    summary = summarize_messages(messages)
    post_summary(summary)

if __name__ == "__main__":
    run_weekly_summary()