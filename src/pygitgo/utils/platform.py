from pygitgo.utils.colors import warning, info
import webbrowser
import subprocess
import platform
import shutil
import os


def get_platform():
    system = platform.system().lower()

    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    elif system == 'linux':
        if is_termux():
            return 'termux'
        return 'linux'
    else:
        return 'unknown'


def is_termux():
    if os.environ.get('PREFIX', '').startswith('/data/data/com.termux'):
        return True

    if os.path.exists('/data/data/com.termux/files/usr'):
        return True

    return False


def open_url(url: str):
    opened = False
    try:
        if is_termux():
            if shutil.which("termux-open"):
                subprocess.run(["termux-open", url], check=False)
                opened = True
        else:
            opened = webbrowser.open(url)
    except Exception:
        opened = False

    if not opened:
        warning("Could not open browser automatically.")
        info("\nIf the browser did not open, visit this URL manually:")
        print(f"\n  {url}\n")

