import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.config import DROPBOX_FOLDER
from src.dropbox_link import get_direct_url
from src.rss_generator import add_episode
from src.uploader import upload_feed


class MP3Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".m4a":
            return
        print(f"[watcher] new file detected: {path.name}")
        self._process(path)

    def on_moved(self, event):
        # Dropbox sometimes writes to a temp file then renames
        if event.is_directory:
            return
        path = Path(event.dest_path)
        if path.suffix.lower() != ".m4a":
            return
        print(f"[watcher] file renamed/moved: {path.name}")
        self._process(path)

    def _process(self, path: Path):
        try:
            print(f"[dropbox] getting shareable link for {path.name}...")
            url = get_direct_url(path.name)
            print(f"[dropbox] url: {url}")
            add_episode(str(path), url)
            upload_feed()
            print(f"[done] {path.name} is now live in the podcast feed.")
        except Exception as e:
            print(f"[error] failed to process {path.name}: {e}")


def main():
    folder = DROPBOX_FOLDER
    print(f"[watcher] watching {folder}")
    observer = Observer()
    observer.schedule(MP3Handler(), path=folder, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
