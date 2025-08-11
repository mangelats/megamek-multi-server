import os.path
from datetime import datetime, timezone


def file_modified(path: str) -> datetime:
    return datetime.fromtimestamp(os.path.getmtime(path), timezone.utc)


def directory_modified(path: str) -> datetime:
    return max(file_modified(de.path) for de in os.scandir(path) if de.is_file())
