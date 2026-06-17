import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import dropbox
import dropbox.exceptions
import dropbox.files
import dropbox.sharing
from feedgen.feed import FeedGenerator
from mutagen.mp4 import MP4

DROPBOX_TOKEN = os.environ["DROPBOX_TOKEN"]
FEED_URL = os.environ["FEED_URL"]
PODCAST_TITLE = os.environ.get("PODCAST_TITLE", "Auto Podcast")
PODCAST_DESCRIPTION = os.environ.get("PODCAST_DESCRIPTION", "Auto-generated podcast from NotebookLM")
EPISODES_FILE = os.environ.get("EPISODES_FILE", "/var/www/autopodcast/episodes.json")
FEED_LOCAL = os.environ.get("FEED_LOCAL", "/var/www/autopodcast/feed.xml")


def _load_episodes() -> list[dict]:
    if os.path.exists(EPISODES_FILE):
        with open(EPISODES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_episodes(episodes: list[dict]) -> None:
    with open(EPISODES_FILE, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)


def _parse_title(filename: str) -> str:
    stem = Path(filename).stem
    return stem.replace("_", " ").title()


def _parse_date(filename: str) -> datetime:
    stem = Path(filename).stem
    date_part = stem.split("_")[0]
    return datetime.strptime(date_part, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _to_direct_url(url: str) -> str:
    url = re.sub(r"https://(www\.dropbox\.com|dl\.dropbox\.com)", "https://dl.dropboxusercontent.com", url)
    url = re.sub(r"[?&]dl=\d", "", url)
    return url


def _get_or_create_link(dbx: dropbox.Dropbox, path: str) -> str:
    try:
        result = dbx.sharing_create_shared_link_with_settings(path)
        return _to_direct_url(result.url)
    except dropbox.exceptions.ApiError as e:
        if e.error.is_shared_link_already_exists():
            links = dbx.sharing_list_shared_links(path=path, direct_only=True).links
            return _to_direct_url(links[0].url)
        raise


def process_new_files() -> None:
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    episodes = _load_episodes()
    known = {ep["filename"] for ep in episodes}

    result = dbx.files_list_folder("")
    entries = list(result.entries)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        entries.extend(result.entries)

    new_files = [
        e for e in entries
        if isinstance(e, dropbox.files.FileMetadata)
        and e.name.lower().endswith(".m4a")
        and e.name not in known
    ]

    if not new_files:
        print("[processor] no new files")
        return

    for entry in new_files:
        print(f"[processor] processing {entry.name}")
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".m4a", delete=False) as tmp:
                tmp_path = tmp.name
            dbx.files_download_to_file(tmp_path, f"/{entry.name}")

            audio = MP4(tmp_path)
            total = int(audio.info.length)
            h, rem = divmod(total, 3600)
            m, s = divmod(rem, 60)
            duration = f"{h:02d}:{m:02d}:{s:02d}"

            url = _get_or_create_link(dbx, f"/{entry.name}")

            episodes.append({
                "filename": entry.name,
                "title": _parse_title(entry.name),
                "date": _parse_date(entry.name).isoformat(),
                "url": url,
                "duration": duration,
                "size": entry.size,
            })
            print(f"[processor] added {entry.name}")
        except Exception as e:
            print(f"[processor] failed {entry.name}: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    episodes.sort(key=lambda e: e["date"], reverse=True)
    _save_episodes(episodes)
    _build_feed(episodes)


def _build_feed(episodes: list[dict]) -> None:
    fg = FeedGenerator()
    fg.load_extension("podcast")
    fg.id(FEED_URL)
    fg.title(PODCAST_TITLE)
    fg.author({"name": PODCAST_TITLE})
    fg.link(href=FEED_URL, rel="self")
    fg.language("en")
    fg.description(PODCAST_DESCRIPTION)
    fg.podcast.itunes_author(PODCAST_TITLE)
    fg.podcast.itunes_explicit("no")

    for ep in episodes:
        fe = fg.add_entry()
        fe.id(ep["url"])
        fe.title(ep["title"])
        fe.published(ep["date"])
        fe.enclosure(ep["url"], str(ep["size"]), "audio/mp4")
        fe.podcast.itunes_duration(ep["duration"])

    fg.rss_file(FEED_LOCAL, pretty=True)
    print(f"[rss] feed updated with {len(episodes)} episode(s)")
