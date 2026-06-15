import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Patch config before importing rss_generator
os.environ.setdefault("DROPBOX_TOKEN", "fake")
os.environ.setdefault("DROPBOX_FOLDER", "/tmp")
os.environ.setdefault("SSH_HOST", "host")
os.environ.setdefault("SSH_USER", "user")
os.environ.setdefault("SSH_KEY_PATH", "/tmp/key")
os.environ.setdefault("SSH_REMOTE_PATH", "/remote/feed.xml")
os.environ.setdefault("FEED_URL", "https://example.com/podcast/feed.xml")
os.environ.setdefault("PODCAST_TITLE", "Test Podcast")
os.environ.setdefault("PODCAST_DESCRIPTION", "Test description")

from src.rss_generator import _parse_date, _parse_title, add_episode


def test_parse_title():
    assert _parse_title("2026-06-15_my_topic.mp3") == "2026-06-15 My Topic"


def test_parse_title_single_word():
    assert _parse_title("2026-06-15_autopodcast.mp3") == "2026-06-15 Autopodcast"


def test_parse_date():
    result = _parse_date("2026-06-15_my_topic.mp3")
    assert result == datetime(2026, 6, 15, tzinfo=timezone.utc)


def test_parse_date_invalid_raises():
    with pytest.raises(ValueError):
        _parse_date("notadate_topic.mp3")


def test_add_episode_deduplication(tmp_path):
    episodes_file = tmp_path / "episodes.json"
    feed_file = tmp_path / "feed.xml"

    with (
        patch("src.rss_generator.EPISODES_FILE", str(episodes_file)),
        patch("src.rss_generator.FEED_LOCAL", str(feed_file)),
        patch("src.rss_generator._get_duration", return_value="00:10:00"),
        patch("src.rss_generator._get_size", return_value=1024),
        patch("src.rss_generator._build_feed"),
    ):
        add_episode("/fake/2026-06-15_topic.mp3", "https://dropbox.com/file.mp3?dl=1")
        add_episode("/fake/2026-06-15_topic.mp3", "https://dropbox.com/file.mp3?dl=1")

        episodes = json.loads(episodes_file.read_text())
        assert len(episodes) == 1


def test_add_episode_sorted_by_date(tmp_path):
    episodes_file = tmp_path / "episodes.json"
    feed_file = tmp_path / "feed.xml"

    with (
        patch("src.rss_generator.EPISODES_FILE", str(episodes_file)),
        patch("src.rss_generator.FEED_LOCAL", str(feed_file)),
        patch("src.rss_generator._get_duration", return_value="00:05:00"),
        patch("src.rss_generator._get_size", return_value=512),
        patch("src.rss_generator._build_feed"),
    ):
        add_episode("/fake/2026-01-01_first.mp3", "https://dropbox.com/first.mp3?dl=1")
        add_episode("/fake/2026-06-15_second.mp3", "https://dropbox.com/second.mp3?dl=1")

        episodes = json.loads(episodes_file.read_text())
        assert episodes[0]["filename"] == "2026-06-15_second.mp3"
        assert episodes[1]["filename"] == "2026-01-01_first.mp3"
