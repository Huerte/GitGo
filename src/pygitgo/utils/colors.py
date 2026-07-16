import sys
import os

def _supports_color():
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False
    if os.environ.get('TERM') == 'dumb':
        return False
    if 'NO_COLOR' in os.environ:
        return False
    if sys.platform == 'win32':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            hOut = kernel32.GetStdHandle(-11)
            if hOut == -1 or hOut is None:
                return False
            mode = ctypes.c_ulong()
            if not kernel32.GetConsoleMode(hOut, ctypes.byref(mode)):
                return False
            if not kernel32.SetConsoleMode(hOut, mode.value | 0x0004):
                return False
            return True
        except Exception:
            return False
    return True

_use_color = _supports_color()

RED = "\033[31m" if _use_color else ""
GREEN = "\033[32m" if _use_color else ""
YELLOW = "\033[33m" if _use_color else ""
BLUE = "\033[34m" if _use_color else ""
CYAN = "\033[36m" if _use_color else ""
RESET = "\033[0m" if _use_color else ""
