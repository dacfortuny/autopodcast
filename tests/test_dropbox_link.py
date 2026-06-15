import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("DROPBOX_TOKEN", "fake")
os.environ.setdefault("DROPBOX_FOLDER", "/tmp")
os.environ.setdefault("SSH_HOST", "host")
os.environ.setdefault("SSH_USER", "user")
os.environ.setdefault("SSH_KEY_PATH", "/tmp/key")
os.environ.setdefault("SSH_REMOTE_PATH", "/remote/feed.xml")
os.environ.setdefault("FEED_URL", "https://example.com/podcast/feed.xml")

from src.dropbox_link import get_direct_url


def test_get_direct_url_new_link():
    mock_result = MagicMock()
    mock_result.url = "https://www.dropbox.com/s/abc/file.mp3?dl=0"

    with patch("src.dropbox_link.dropbox.Dropbox") as MockDropbox:
        MockDropbox.return_value.sharing_create_shared_link_with_settings.return_value = mock_result
        url = get_direct_url("file.mp3")

    assert url == "https://www.dropbox.com/s/abc/file.mp3?dl=1"


def test_get_direct_url_already_exists():
    import dropbox.exceptions

    existing_url = MagicMock()
    existing_url.url = "https://www.dropbox.com/s/abc/file.mp3?dl=0"

    mock_error = MagicMock()
    mock_error.is_shared_link_already_exists.return_value = True
    mock_error.get_shared_link_already_exists.return_value.metadata.url = existing_url.url

    api_error = dropbox.exceptions.ApiError("req", mock_error, "user_msg", "en")

    with patch("src.dropbox_link.dropbox.Dropbox") as MockDropbox:
        MockDropbox.return_value.sharing_create_shared_link_with_settings.side_effect = api_error
        url = get_direct_url("file.mp3")

    assert url == "https://www.dropbox.com/s/abc/file.mp3?dl=1"
