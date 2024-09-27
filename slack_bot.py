from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
from dotenv import load_dotenv
from jira import JIRA
import json

load_dotenv()

SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
JIRA_SERVER = os.getenv("JIRA_SERVER")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

slack = App(
    token=SLACK_APP_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

jira = JIRA(server=JIRA_SERVER, basic_auth=(JIRA_USERNAME, JIRA_API_TOKEN))

def search_jira(query):
    return jira.search_issues(f'text ~ "{query}"', maxResults=10)

def create_jira_issue(project_key, title, desc, type, slack_msg_link = None):
    if slack_msg_link is not None:
        desc += f"\nSlack thread: {slack_msg_link}"

    fields = {
        "project": project_key,
        "summary": f"#production-feedback: {title}",
        "description": desc,
        "issuetype": {'name': type},
    }
    issue = jira.create_issue(fields=fields)
    jira.add_comment(issue, "This issue was created by FeedbackPulse, an FBG Slack Bot. For more information, see: https://betfanatics.atlassian.net/wiki/spaces/~640b4f59896d10ebd4750c3f/pages/988708869/Project+SAHN+Stop+After-Hours+Nagging")
    return issue

def get_permalink(message):
    slack_msg_permalink = slack.client.chat_getPermalink(
        channel=message["channel"],
        message_ts=message["ts"]
    )
    return slack_msg_permalink['permalink']

#wip this currently replies to everything!
@slack.message(".*")
def say_hello(message, say):
    print(f"message received: {json.dumps(message, indent=2)}")

    jira_issue = create_jira_issue("PROF", "SlackBot Test", "This is a test issue, it can be closed", "Bug", get_permalink(message))
    reply = {
        "text":
            f"""
            Good news, <@{message['user']}>!\n\nI created a JIRA issue from this message: {jira_issue.permalink()}
            """,
        "thread_ts": message["ts"]
    }
    say(reply)

if __name__ == "__main__":
    SocketModeHandler(slack, SLACK_BOT_TOKEN).start()
    # print("\nMatching Jira Issues:")
    # for issue in search_jira("native login"):
    #     print(f"- {issue.key}: {issue.fields.summary}")

