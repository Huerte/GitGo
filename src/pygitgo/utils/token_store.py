"""Where GitGo keeps the GitHub token.

Order of preference:
1. Git's own credential helper (macOS Keychain, Windows Credential Manager,
   libsecret, ...), under a private host name so it never mixes with the
   user's normal github.com credentials.
2. A file readable only by the current user, when no helper stored it.

The old location, `git config --global gitgo.github-token`, is plaintext in
~/.gitconfig. load_token() moves any token found there into the new place and
removes the old entry.
"""
import os
import stat
import subprocess
from pathlib import Path

_CRED_HOST = "token.gitgo.invalid"
_CRED_USER = "gitgo"
_LEGACY_KEY = "gitgo.github-token"


def _token_file() -> Path:
    base = os.environ.get("APPDATA") if os.name == "nt" else None
    root = Path(base) if base else Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return root / "gitgo" / "token"


_HELPER_TIMEOUT = 4
_helper_broken = False  # set when a helper call hangs, so we stop asking for this run


def _helper_env():
    env = dict(os.environ)
    env.update(
        GIT_TERMINAL_PROMPT="0",
        GCM_INTERACTIVE="never",
        # An askpass program (VS Code and some terminals set one) can pop up a window
        # and wait for a person. Empty values stop git from calling it at all.
        GIT_ASKPASS="",
        SSH_ASKPASS="",
    )
    return env


def _kill_tree(proc):
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True, timeout=5)
        else:
            proc.kill()
    except Exception:
        pass


def _helper_enabled() -> bool:
    return not _helper_broken and os.environ.get("GITGO_NO_CREDENTIAL_HELPER", "").strip() not in ("1", "true", "yes")


def _helper_run(action: str, token: str = ""):
    """Run `git credential <action>`. Never blocks for long and never raises.

    Returns the CompletedProcess-like result, or None when the helper is disabled,
    missing, or hung (in which case it stays disabled for the rest of this run).
    """
    global _helper_broken
    if not _helper_enabled():
        return None

    fields = f"protocol=https\nhost={_CRED_HOST}\nusername={_CRED_USER}\n"
    if action == "approve":
        fields += f"password={token}\n"

    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        proc = subprocess.Popen(
            ["git", "credential", action],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=_helper_env(), **kwargs,
        )
    except OSError:
        _helper_broken = True
        return None

    try:
        out, err = proc.communicate(fields + "\n", timeout=_HELPER_TIMEOUT)
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        try:
            proc.communicate(timeout=2)
        except Exception:
            pass
        _helper_broken = True
        return None
    except Exception:
        _kill_tree(proc)
        _helper_broken = True
        return None
    return subprocess.CompletedProcess(proc.args, proc.returncode, out, err)


def _helper_load() -> str:
    result = _helper_run("fill")
    if not result or result.returncode != 0:
        return ""
    for line in result.stdout.splitlines():
        if line.startswith("password="):
            return line[len("password="):].strip()
    return ""


def _file_save(token: str):
    path = _token_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(str(path), flags, stat.S_IRUSR | stat.S_IWUSR)
    with os.fdopen(fd, "w") as f:
        f.write(token)
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def _file_load() -> str:
    try:
        return _token_file().read_text().strip()
    except OSError:
        return ""


def _legacy_load() -> str:
    try:
        r = subprocess.run(["git", "config", "--global", _LEGACY_KEY],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _legacy_clear():
    try:
        subprocess.run(["git", "config", "--global", "--unset-all", _LEGACY_KEY],
                       capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def save_token(token: str) -> str:
    """Store the token. Returns where it went: 'credential-helper' or 'file'."""
    _helper_run("reject")  # drop any older value first
    _helper_run("approve", token)
    if _helper_load() == token:
        _file_delete()
        return "credential-helper"
    _file_save(token)
    return "file"


def load_token() -> str:
    token = _helper_load() or _file_load()
    if token:
        return token
    legacy = _legacy_load()
    if legacy:
        save_token(legacy)
        _legacy_clear()
    return legacy


def _file_delete():
    try:
        _token_file().unlink()
    except OSError:
        pass


def delete_token():
    _helper_run("reject")
    _file_delete()
    _legacy_clear()
