# autopodcast

Automatically publishes NotebookLM audio overviews as a private podcast. Upload a `.m4a` to Dropbox via the web, and a new episode appears in your podcast app within seconds.

## How it works

1. Export an audio overview from NotebookLM, rename it `YYYY-MM-DD_title.m4a`, and upload it to your Dropbox App folder via the web
2. Dropbox notifies the webhook running on your server
3. The server creates a direct Dropbox download link via the API
4. It adds the episode to `feed.xml` (persisted in `episodes.json`)
5. Your podcast app picks up the new episode on its next refresh

## Subscribe

| App | Link |
|-----|------|
| Apple Podcasts | `podcast://deltadedidac.cat/podcast/feed.xml` |
| Overcast | `overcast://x-callback-url/add?url=https://deltadedidac.cat/podcast/feed.xml` |
| Pocket Casts | `pktc://subscribe/deltadedidac.cat/podcast/feed.xml` |
| Any app | paste `https://deltadedidac.cat/podcast/feed.xml` in "Add by URL" |

## File naming convention

Files must follow `YYYY-MM-DD_title.m4a`, e.g. `2026-06-17_my_topic.m4a`. The episode title is derived from the filename: underscores become spaces, title-cased.

---

## Server setup (one-time)

The webhook listener runs on `deltadedidac.cat` as a systemd service.

### 1. Clone the repo on the server

```bash
git clone https://github.com/dacfortuny/autopodcast.git /var/www/autopodcast/repo
```

### 2. Install dependencies

```bash
cd /var/www/autopodcast/repo/server
uv venv
uv pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
nano .env
```

```env
DROPBOX_TOKEN=your_dropbox_api_token
DROPBOX_APP_SECRET=your_dropbox_app_secret
FEED_URL=https://deltadedidac.cat/podcast/feed.xml
PODCAST_TITLE=My Podcast
PODCAST_DESCRIPTION=Auto-generated podcast from NotebookLM
EPISODES_FILE=/var/www/autopodcast/episodes.json
FEED_LOCAL=/var/www/autopodcast/feed.xml
```

Find `DROPBOX_APP_SECRET` in the [Dropbox App Console](https://www.dropbox.com/developers/apps) → Settings → App secret → Show.

### 4. systemd service

```bash
nano /etc/systemd/system/autopodcast.service
```

```ini
[Unit]
Description=Autopodcast webhook
After=network.target

[Service]
WorkingDirectory=/var/www/autopodcast/repo/server
EnvironmentFile=/var/www/autopodcast/repo/server/.env
ExecStart=/var/www/autopodcast/repo/server/.venv/bin/gunicorn --workers 1 --bind 127.0.0.1:5000 webhook:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now autopodcast
```

### 5. nginx

Add inside your existing `server {}` block:

```nginx
location /webhook {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
}

location /podcast/ {
    alias /var/www/autopodcast/;
}
```

```bash
nginx -t && systemctl reload nginx
```

### 6. Register the Dropbox webhook

In the [Dropbox App Console](https://www.dropbox.com/developers/apps) → your app → **Webhooks** tab, add:

```
https://deltadedidac.cat/webhook
```

Dropbox verifies it immediately. Once it shows **Enabled**, the pipeline is live.

### Updating the code

```bash
cd /var/www/autopodcast/repo
git pull
systemctl restart autopodcast
```

---

## Stack

- [dropbox](https://github.com/dropbox/dropbox-sdk-python) — creates direct download links and lists folder changes
- [feedgen](https://github.com/lkiesow/python-feedgen) — generates RSS XML
- [flask](https://flask.palletsprojects.com) + [gunicorn](https://gunicorn.org) — webhook listener
- [mutagen](https://github.com/quodlibet/mutagen) — reads audio duration
