import time

import dropbox
import dropbox.exceptions
import dropbox.sharing
from src.config import DROPBOX_TOKEN


def _to_direct_url(url: str) -> str:
    # Replace dl.dropbox.com or www.dropbox.com host with dl.dropboxusercontent.com
    # and strip the dl= parameter entirely — this gives a true direct-download URL.
    import re
    url = re.sub(r'https://(www\.dropbox\.com|dl\.dropbox\.com)', 'https://dl.dropboxusercontent.com', url)
    url = re.sub(r'[?&]dl=\d', '', url)
    return url


def get_direct_url(filename: str) -> str:
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    path = f"/{filename}"
    for attempt in range(10):
        try:
            result = dbx.sharing_create_shared_link_with_settings(path)
            return _to_direct_url(result.url)
        except dropbox.exceptions.ApiError as e:
            error = e.error
            if error.is_shared_link_already_exists():
                links = dbx.sharing_list_shared_links(path=path, direct_only=True).links
                return _to_direct_url(links[0].url)
            if error.is_path() and error.get_path().is_not_found():
                print(f"[dropbox] file not yet synced, retrying in 5s (attempt {attempt + 1}/10)...")
                time.sleep(5)
                continue
            raise
    raise RuntimeError(f"Dropbox file not found after 50s: {filename}")
