import os
from dotenv import load_dotenv

load_dotenv()

DROPBOX_TOKEN = os.environ["DROPBOX_TOKEN"]
DROPBOX_FOLDER = os.environ["DROPBOX_FOLDER"]

SSH_HOST = os.environ["SSH_HOST"]
SSH_USER = os.environ["SSH_USER"]
SSH_KEY_PATH = os.path.expanduser(os.environ.get("SSH_KEY_PATH", "")) if os.environ.get("SSH_KEY_PATH") else None
SSH_PASSWORD = os.environ.get("SSH_PASSWORD")
SSH_REMOTE_PATH = os.environ["SSH_REMOTE_PATH"]

FEED_URL = os.environ["FEED_URL"]
PODCAST_TITLE = os.environ.get("PODCAST_TITLE", "Auto Podcast")
PODCAST_DESCRIPTION = os.environ.get("PODCAST_DESCRIPTION", "Auto-generated podcast from NotebookLM")

EPISODES_FILE = os.path.join(os.path.dirname(__file__), "..", "episodes.json")
FEED_LOCAL = os.path.join(os.path.dirname(__file__), "..", "feed.xml")
