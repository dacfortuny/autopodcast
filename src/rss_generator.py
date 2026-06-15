import json
import os
from datetime import datetime, timezone
from pathlib import Path

from feedgen.feed import FeedGenerator
from mutagen.mp4 import MP4

from src.config import (
    EPISODES_FILE,
    FEED_LOCAL,
    FEED_URL,
    PODCAST_DESCRIPTION,
    PODCAST_TITLE,
)


def _load_episodes() -> list[dict]:
    if os.path.exists(EPISODES_FILE):
        with open(EPISODES_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_episodes(episodes: list[dict]) -> None:
    with open(EPISODES_FILE, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)


def _parse_title(filename: str) -> str:
    stem = Path(filename).stem  # e.g. "2025-01-01_autopodcast"
    return stem.replace("_", " ").title()


def _parse_date(filename: str) -> datetime:
    stem = Path(filename).stem
    date_part = stem.split("_")[0]  # "2025-01-01"
    return datetime.strptime(date_part, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _get_duration(filepath: str) -> str:
    audio = MP4(filepath)
    total = int(audio.info.length)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _get_size(filepath: str) -> int:
    return os.path.getsize(filepath)


def add_episode(filepath: str, url: str) -> None:
    filename = Path(filepath).name
    episodes = _load_episodes()

    if any(ep["filename"] == filename for ep in episodes):
        return

    episode = {
        "filename": filename,
        "title": _parse_title(filename),
        "date": _parse_date(filename).isoformat(),
        "url": url,
        "duration": _get_duration(filepath),
        "size": _get_size(filepath),
    }
    episodes.append(episode)
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
    print(f"[rss] feed updated with {len(episodes)} episode(s) → {FEED_LOCAL}")
