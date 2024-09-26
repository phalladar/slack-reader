from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
from dotenv import load_dotenv

load_dotenv()

SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

app = App(
    token=SLACK_APP_TOKEN,
    signing_secret=SLACK_SIGNING_SECRET
)

@app.message(".*")
def say_hello(message, say):
    print(message)
    user = message['user']
    say(f"Hi <@{user}>!")

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_BOT_TOKEN).start()
