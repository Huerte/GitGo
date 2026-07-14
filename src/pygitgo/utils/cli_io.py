from pygitgo.utils.colors import RED, GREEN, YELLOW, BLUE, CYAN, RESET
import shutil

_QUIET = False
_VERBOSE = False

def confirm(prompt, destructive=False):
    prefix = ""
    if destructive:
        prefix = f"{RED}DANGER: {RESET}"
    user_input = input(f"{prefix}{prompt}").strip().lower()
    return user_input in ('y', 'yes')

def danger(msg):
    print(f"{RED}DANGER: {msg.strip()}{RESET}")

def error(msg):
    print(f"{RED}{msg.strip()}{RESET}")

def warning(msg):
    if _QUIET:
        return
    print(f"{YELLOW}WARNING: {msg.strip()}{RESET}")

def info(msg):
    if _QUIET:
        return
    print(f"{BLUE}{msg.strip()}{RESET}")

def success(msg):
    if _QUIET:
        return
    print(f"{GREEN}{msg.strip()}{RESET}")

def banner(title, subtitle=""):
    if _QUIET:
        return
    width = min(shutil.get_terminal_size().columns, 72)
    print()
    print(GREEN + ("=" * width) + RESET)
    print(GREEN + title.center(width) + RESET)
    if subtitle:
        print(CYAN + subtitle.center(width) + RESET)
    print(GREEN + ("=" * width) + RESET)
    print()

def write(msg="", end="\n"):
    if _QUIET:
        return
    print(msg, end=end)

def set_verbosity(quiet=False, verbose=False):
    global _QUIET, _VERBOSE
    _QUIET = quiet 
    _VERBOSE = verbose





