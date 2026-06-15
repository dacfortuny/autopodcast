# autopodcast

Watches a local Dropbox folder for new `.m4a` files (exported from NotebookLM), creates direct Dropbox download links, builds an RSS feed, and uploads it to a server — so any podcast app can subscribe.

## How it works

1. Export an audio overview from NotebookLM and save the `.m4a` to your Dropbox App folder
2. The watcher detects the new file
3. It creates a direct Dropbox download link via the API
4. It adds the episode to `feed.xml` (persisted in `episodes.json`)
5. It uploads `feed.xml` to your server via SFTP
6. Your podcast app picks up the new episode on its next refresh

## Setup

### 1. Create a Dropbox app

Go to [dropbox.com/developers/apps](https://www.dropbox.com/developers/apps) and create an app with **App folder** access. Note the folder name Dropbox creates locally (e.g. `Apps/your-app-name`). Generate an access token.

### 2. Install dependencies

```powershell
uv sync
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in:

```env
DROPBOX_TOKEN=your_dropbox_api_token
DROPBOX_FOLDER=C:\Users\you\Didac\Dropbox\Apps\your-app-folder

SSH_HOST=your-server.com
SSH_USER=root
SSH_PASSWORD=your_ssh_password
SSH_REMOTE_PATH=/var/www/autopodcast/feed.xml

FEED_URL=https://your-server.com/podcast/feed.xml
PODCAST_TITLE=My Podcast
PODCAST_DESCRIPTION=Auto-generated podcast from NotebookLM
```

> **Note:** Find your actual Dropbox path in `%LOCALAPPDATA%\Dropbox\info.json` → `personal.path`.

### 4. Server setup (one-time)

```bash
mkdir -p /var/www/autopodcast
```

Add to your nginx server block:

```nginx
location /podcast/ {
    alias /var/www/autopodcast/;
}
```

Then reload: `nginx -s reload`

### 5. Run

```powershell
uv run python -u watcher.py
```

Subscribe your podcast app to `https://your-server.com/podcast/feed.xml`.

## File naming convention

Files must follow `YYYY-MM-DD_title.m4a`, e.g. `2026-06-15_my_topic.m4a`. The episode title is derived from the filename: underscores become spaces, title-cased.

## Stack

- [watchdog](https://github.com/gorakhargosh/watchdog) — monitors the Dropbox folder
- [dropbox](https://github.com/dropbox/dropbox-sdk-python) — creates direct download links via API
- [feedgen](https://github.com/lkiesow/python-feedgen) — generates RSS XML
- [mutagen](https://github.com/quodlibet/mutagen) — reads audio duration
- [paramiko](https://github.com/paramiko/paramiko) — SFTP upload
