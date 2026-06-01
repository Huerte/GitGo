import platform
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
