import hashlib
import hmac
import os
import threading

from dotenv import load_dotenv
from flask import Flask, abort, request

load_dotenv()

from processor import process_new_files

app = Flask(__name__)
DROPBOX_APP_SECRET = os.environ["DROPBOX_APP_SECRET"]
_lock = threading.Lock()


@app.route("/webhook", methods=["GET"])
def verify():
    # Dropbox sends this once when you register the webhook URL
    return request.args.get("challenge", ""), 200, {"Content-Type": "text/plain"}


@app.route("/webhook", methods=["POST"])
def notify():
    sig = request.headers.get("X-Dropbox-Signature", "")
    expected = hmac.new(DROPBOX_APP_SECRET.encode(), request.data, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        abort(403)
    # Return 200 immediately; Dropbox retries if we take too long
    threading.Thread(target=_run_processor, daemon=True).start()
    return "", 200


def _run_processor():
    with _lock:
        try:
            process_new_files()
        except Exception as e:
            print(f"[processor] error: {e}")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
