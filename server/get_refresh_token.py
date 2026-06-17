"""
Run this once locally to get a refresh token for your Dropbox app.
You need APP_KEY and APP_SECRET from the Dropbox App Console.

Usage:
    uv run python server/get_refresh_token.py
"""
import os
import dropbox
from dotenv import load_dotenv

load_dotenv("server/.env")

APP_KEY = os.environ["DROPBOX_APP_KEY"]
APP_SECRET = os.environ["DROPBOX_APP_SECRET"]

auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(
    APP_KEY, APP_SECRET, token_access_type="offline"
)

url = auth_flow.start()
print("1. Go to:", url)
print("2. Click 'Allow'")
print("3. Paste the code below\n")
code = input("Enter the authorization code: ").strip()

result = auth_flow.finish(code)
print(f"\nRefresh token: {result.refresh_token}")
print("\nAdd this to your server .env as DROPBOX_REFRESH_TOKEN=<token above>")
