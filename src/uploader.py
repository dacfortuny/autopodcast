import paramiko
from src.config import FEED_LOCAL, SSH_HOST, SSH_KEY_PATH, SSH_PASSWORD, SSH_REMOTE_PATH, SSH_USER


def upload_feed() -> None:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username=SSH_USER, key_filename=SSH_KEY_PATH, password=SSH_PASSWORD)
    sftp = ssh.open_sftp()
    sftp.put(FEED_LOCAL, SSH_REMOTE_PATH)
    sftp.close()
    ssh.close()
    print(f"[upload] feed.xml → {SSH_HOST}:{SSH_REMOTE_PATH}")
