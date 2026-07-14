from pygitgo.utils.cli_io import info, warning, write
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.error
import threading
import json



CACHE_DIR = Path.home() / ".gitgo"
CACHE_FILE = CACHE_DIR / "update_check.json"
PYPI_URL = "https://pypi.org/pypi/pygitgo/json"
CHECK_INTERVAL = timedelta(days=7)
REQUEST_TIMEOUT = 2


def read_cache():
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def write_cache(data):
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f)
    except IOError:
        pass


def should_check():
    cache = read_cache()
    last_check = cache.get("last_check")

    if not last_check:
        return True

    try:
        last_check_time = datetime.fromisoformat(last_check)
        return (datetime.now() - last_check_time) > CHECK_INTERVAL
    except ValueError:
        return True


def get_latest_version():
    try:
        with urllib.request.urlopen(PYPI_URL, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["info"]["version"]
    except Exception:
        return None


def parse_version(version_string):
    parts = [int(x) for x in version_string.split(".")]
    while len(parts) < 3:
        parts.append(0)
    return parts


def check_for_updates(current_version):
    if not should_check():
        return

    cache = read_cache()
    cache["last_check"] = datetime.now().isoformat()
    write_cache(cache)

    latest_version = get_latest_version()
    if not latest_version or latest_version == current_version:
        return

    try:
        current_parts = parse_version(current_version)
        latest_parts = parse_version(latest_version)

        if latest_parts > current_parts:
            write()
            warning(f"GitGo update available: {current_version} -> {latest_version}")
            info("Run: pip install --upgrade pygitgo")
            write()

            cache["notified_version"] = latest_version
            write_cache(cache)
    except (ValueError, AttributeError):
        pass


def check_for_updates_background(current_version):
    thread = threading.Thread(target=check_for_updates, args=(current_version,), daemon=True)
    thread.start()
