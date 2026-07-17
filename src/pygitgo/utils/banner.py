from pygitgo.commands.git_core import ensure_inside_git_repository, get_recent_commits
from pygitgo.utils.colors import GREEN, YELLOW, CYAN, RESET
from pygitgo.utils.update_checker import check_for_updates
from pygitgo.commands.git_branch import get_current_branch
from pygitgo.utils.executor import run_command
from pygitgo.auth.account import get_user
import shutil


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default

def _format_sync():
    """Human readable ahead/behind summary, or None if no upstream is tracked."""
    try:
        raw = run_command(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"])
    except Exception:
        return None

    parts = raw.split()
    if len(parts) != 2:
        return None
    ahead, behind = int(parts[0]), int(parts[1])

    if ahead == 0 and behind == 0:
        return f"{GREEN}up to date{RESET}"
    if ahead and not behind:
        return f"{YELLOW}{ahead} ahead{RESET}"
    if behind and not ahead:
        return f"{YELLOW}{behind} behind{RESET}"
    return f"{YELLOW}{ahead} ahead, {behind} behind (diverged){RESET}"

def show_banner():
    from pygitgo.main import get_version

    ensure_inside_git_repository()

    username, email = get_user()
    username = username or "Not set"
    email = email or "Not set"
    remote_url = _safe(lambda: run_command("git config --get remote.origin.url".split())) or "not set"
    current_branch = _safe(get_current_branch) or "unknown"
    sync_msg = _format_sync() or f"{YELLOW}no upstream{RESET}"

    porcelain = run_command(["git", "status", "--porcelain"])
    lines = [line for line in porcelain.splitlines() if line.strip()]
    untracked = sum(1 for line in lines if line.startswith("??"))
    modified = len(lines) - untracked

    if modified == 0 and untracked == 0:
        status_msg = f"{GREEN}clean{RESET}"
    else:
        parts = []
        if modified:
            parts.append(f"{modified} modified")
        if untracked:
            parts.append(f"{untracked} untracked")
        status_msg = f"{YELLOW}{', '.join(parts)}{RESET}"

    commits = _safe(lambda: get_recent_commits(number=1))
    if commits:
        c = commits[0]
        latest = f"[{YELLOW}{c['hash']}{RESET}] {c['message']} ({CYAN}{c['date']}{RESET}) by {GREEN}{c['author']}{RESET}"
    else:
        latest = "no commits yet"

    version = get_version()
    cached = check_for_updates(version)

    # auto-width box so it never overflows narrow terminals (e.g. Termux)
    width = max(46, min(shutil.get_terminal_size((80, 20)).columns - 2, 70))
    top = "╭" + "─" * (width - 2) + "╮"
    title = f"│{f' GitGo {version} '.center(width - 2)}│"
    subtitle = f"│{'Your Fast Git Companion'.center(width - 2)}│"
    bottom = "╰" + "─" * (width - 2) + "╯"

    rows = [
        ("Identity", f"{username} <{email}>"),
        ("Remote", remote_url),
        ("Branch", current_branch),
        ("Sync", sync_msg),
        ("Status", status_msg),
        ("Latest", latest),
    ]
    label_width = max(len(label) for label, _ in rows)

    out = [top, title, subtitle, bottom, ""]
    for label, value in rows:
        out.append(f"  {label.ljust(label_width)}  {value}")

    out += [
        "",
        "  PyPI     pypi.org/project/pygitgo",
        "  GitHub   github.com/Huerte/GitGo",
        "  Sponsor  github.com/sponsors/Huerte",
    ]
    if cached:
        out += ["", str(cached)]
    out += ["", f"  Run {GREEN}`gitgo help`{RESET} to see available commands.", ""]

    print("\n".join(out))
