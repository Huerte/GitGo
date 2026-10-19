from pygitgo.utils.colors import RED, GREEN, YELLOW, BLUE, CYAN, RESET
import shutil
import sys
import re


_QUIET = False
_VERBOSE = False


_ASCII_FALLBACK = str.maketrans({
    "╭": "+", "╮": "+", "╰": "+", "╯": "+", "─": "-", "│": "|",
    "✔": "OK", "✖": "X", "→": "->",
})


def _stdout_encoding():
    return getattr(sys.stdout, "encoding", None) or "ascii"


def _can_encode(text):
    try:
        text.encode(_stdout_encoding())
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def ok_mark():
    """Check mark for spinners; falls back to ASCII on legacy encodings."""
    return "✔" if _can_encode("✔") else "OK"


def fail_mark():
    return "✖" if _can_encode("✖") else "X"


def safe_print(msg="", end="\n", file=None):
    """print() that never crashes on terminals/pipes that can't encode box-drawing chars."""
    kwargs = {"end": end}
    if file is not None:
        kwargs["file"] = file
    try:
        print(msg, **kwargs)
    except UnicodeEncodeError:
        stream = file or sys.stdout
        enc = getattr(stream, "encoding", None) or "ascii"
        text = str(msg).translate(_ASCII_FALLBACK).encode(enc, errors="replace").decode(enc, errors="replace")
        print(text, **kwargs)


_CMD_PATTERN = re.compile(r"(gitgo(?:[ ][\w./-]+)+)")

def _highlight_cmd(msg, resume_color=""):
    def replacer(m):
        return f"{GREEN}{m.group(1)}{RESET}{resume_color}"
    return _CMD_PATTERN.sub(replacer, msg)

def confirm(prompt, destructive=False):
    prefix = ""
    if destructive:
        prefix = f"{RED}DANGER: {RESET}"
    user_input = input(f"{prefix}{prompt}").strip().lower()
    return user_input in ('y', 'yes')

def danger(msg):
    safe_print(f"{RED}DANGER: {msg.strip()}{RESET}")

def error(msg):
    safe_print(f"{RED}{msg.strip()}{RESET}", file=sys.stderr)

def warning(msg, required=False):
    if _QUIET and not required:
        return
    safe_print(f"{YELLOW}WARNING: {_highlight_cmd(msg.strip(), YELLOW)}{RESET}", file=sys.stderr)

def info(msg, required=False):
    if _QUIET and not required:
        return
    safe_print(f"{BLUE}{_highlight_cmd(msg.strip(), BLUE)}{RESET}")

def success(msg, required=False):
    if _QUIET and not required:
        return
    safe_print(f"{GREEN}{msg.strip()}{RESET}")

def banner(title, subtitle="", required=False):
    if _QUIET and not required:
        return
    width = max(46, min(shutil.get_terminal_size((80, 20)).columns - 2, 70))
    inner_width = width - 2

    top = GREEN + "╭" + "─" * inner_width + "╮" + RESET

    plain_title = title.strip()
    padding_title = inner_width - len(plain_title)
    if padding_title > 0:
        left_title = padding_title // 2
        right_title = padding_title - left_title
        title_line = GREEN + "│" + RESET + " " * left_title + GREEN + plain_title + RESET + " " * right_title + GREEN + "│" + RESET
    else:
        title_line = GREEN + "│" + RESET + plain_title[:inner_width] + GREEN + "│" + RESET

    sub_line = None
    if subtitle:
        plain_sub = subtitle.strip()
        padding_sub = inner_width - len(plain_sub)
        if padding_sub > 0:
            left_sub = padding_sub // 2
            right_sub = padding_sub - left_sub
            sub_line = GREEN + "│" + RESET + " " * left_sub + CYAN + plain_sub + RESET + " " * right_sub + GREEN + "│" + RESET
        else:
            sub_line = GREEN + "│" + RESET + plain_sub[:inner_width] + GREEN + "│" + RESET

    bottom = GREEN + "╰" + "─" * inner_width + "╯" + RESET

    safe_print()
    safe_print(top)
    safe_print(title_line)
    if sub_line:
        safe_print(sub_line)
    safe_print(bottom)
    safe_print()


def write(msg="", end="\n", required=False):
    if _QUIET and not required:
        return
    safe_print(_highlight_cmd(str(msg)) if msg else msg, end=end)

def set_verbosity(quiet=False, verbose=False):
    global _QUIET, _VERBOSE
    _QUIET = quiet
    _VERBOSE = verbose
