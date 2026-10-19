from pygitgo.exceptions import GitCommandError, GitGoError
from .host_keys import PINNED_HOSTS, known_hosts_lines, host_key_types_present
from pygitgo.utils.cli_io import info, success, warning, ok_mark, fail_mark
from pygitgo.utils.platform import get_platform
from pygitgo.utils.executor import run_command
from pathlib import Path
from typing import Optional
import subprocess
import shutil
import time
import os
import re


SSH_TIMEOUT_SECONDS = 10

_cached_ssh_response = None
_cache_populated = False


def get_remote_host(url: str) -> Optional[str]:
    """Return the hostname from an SSH or HTTPS remote URL."""
    url = url.strip()
    # git@host:owner/repo.git
    ssh_match = re.match(r"git@([^:]+):", url)
    if ssh_match:
        return ssh_match.group(1)
    # https://host/owner/repo or http://host/owner/repo
    https_match = re.match(r"https?://([^/]+)", url)
    if https_match:
        return https_match.group(1)
    return None


def ensure_known_host(host: str = "github.com"):
    """Make sure `host` is in known_hosts.

    github.com is filled from GitHub's published keys (see host_keys.py), so nothing
    on the network gets to decide what we trust. Other hosts still fall back to
    ssh-keyscan, which trusts whatever answers on first connect.
    """
    known_hosts = Path.home() / ".ssh" / "known_hosts"
    known_hosts.parent.mkdir(parents=True, exist_ok=True)

    try:
        existing = known_hosts.read_text() if known_hosts.exists() else ""
    except OSError:
        existing = ""

    present = host_key_types_present(existing, host)

    if host in PINNED_HOSTS:
        missing = [line for line in known_hosts_lines(host) if line.split()[1] not in present]
        if not missing:
            return
        try:
            with open(known_hosts, "a") as f:
                if existing and not existing.endswith("\n"):
                    f.write("\n")
                f.write("\n".join(missing) + "\n")
            success(f"{host} host keys added to known_hosts (GitHub's published keys).")
        except OSError:
            warning(f"Could not write {known_hosts}. You might be prompted to verify {host}.")
        return

    if present:
        return

    info(f"Adding {host} to known_hosts...")
    warning(f"{host}'s key is taken from the network on first connect. Verify it if you can.")
    try:
        result = run_command(["ssh-keyscan", "-H", host], return_complete=True)
        if result.stdout and host in result.stdout:
            with open(known_hosts, "a") as f:
                f.write(result.stdout)
                if not result.stdout.endswith("\n"):
                    f.write("\n")
            success(f"{host} added to known_hosts.")
    except GitCommandError:
        warning(f"Could not automatically add {host} to known_hosts. You might be prompted.")


# Keep the old name so existing callers do not break.
def ensure_github_known_host():
    ensure_known_host("github.com")


def _get_ssh_response(host: str = "github.com"):
    """Test SSH connectivity to the given host."""
    try:
        result = subprocess.run(
            ["ssh", "-T", "-o", "BatchMode=yes", f"git@{host}"],
            capture_output=True, text=True,
            timeout=SSH_TIMEOUT_SECONDS, stdin=subprocess.DEVNULL,
        )
        combined = (result.stderr or "") + (result.stdout or "")
        return combined, False, None
    except subprocess.TimeoutExpired:
        return "", True, None
    except OSError as e:
        return "", False, str(e)


# Keep module-level cache for GitHub only (used by login flow).
def _get_github_ssh_response():
    return _get_ssh_response("github.com")


def _get_cached_ssh_response():
    global _cached_ssh_response, _cache_populated
    if not _cache_populated:
        _cached_ssh_response = _get_github_ssh_response()
        _cache_populated = True
    return _cached_ssh_response  # (raw_output, timed_out, os_error)


def clear_ssh_cache():
    global _cached_ssh_response, _cache_populated
    _cached_ssh_response = None
    _cache_populated = False


def classify_connection_error(raw_output: str, timed_out: bool, os_error: Optional[str]) -> str:
    """Return a short, plain-English reason for a connection failure."""
    if timed_out:
        return "Connection timed out. Port 22 may be blocked by your network or firewall."
    if os_error:
        return f"Could not start SSH: {os_error}"
    if not raw_output:
        return "No response from the server. Check your internet connection."
    if "Permission denied" in raw_output:
        return "Permission denied. Your SSH key was not accepted by the server."
    if "Connection refused" in raw_output:
        return "Connection refused on port 22. Try a network without strict firewall rules."
    if "Host key verification failed" in raw_output:
        return (
            "Host key check failed. The key in ~/.ssh/known_hosts does not match what the server sent. "
            "This can mean a man-in-the-middle, or GitHub rotated its keys. Compare against "
            "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints "
            "before removing the old line with: ssh-keygen -R <host>"
        )
    if "Could not resolve hostname" in raw_output:
        return "DNS lookup failed. You may be offline or behind a proxy."
    return raw_output.strip() or "Unknown SSH error."


def check_connection(ok_text=None, fail_text=None, host: str = "github.com"):
    """Check SSH connectivity to a given host. Defaults to github.com."""
    from yaspin import yaspin
    import sys

    ensure_known_host(host)

    kwargs = {"text": f"Checking connection to {host}..."}
    if sys.stdout.isatty():
        kwargs["color"] = "cyan"
    spinner = yaspin(**kwargs)
    spinner.start()

    try:
        if host == "github.com":
            raw_output, timed_out, os_error = _get_cached_ssh_response()
        else:
            raw_output, timed_out, os_error = _get_ssh_response(host)
    except KeyboardInterrupt:
        spinner.stop()
        raise

    connected = (
        not timed_out
        and not os_error
        and "successfully authenticated" in raw_output
    )

    if connected:
        spinner.text = ok_text or f"Connected to {host}."
        spinner.ok(ok_mark())
    else:
        spinner.text = fail_text or f"Could not connect to {host}."
        spinner.fail(fail_mark())

    return connected


def get_github_username():
    raw_output, _timed_out, _os_error = _get_cached_ssh_response()
    if raw_output and "Hi " in raw_output and "!" in raw_output:
        try:
            return raw_output.split("Hi ")[1].split("!")[0]
        except (IndexError, ValueError):
            pass
    return None


GITGO_KEY_NAME = "gitgo_ed25519"
LEGACY_KEY_NAME = "id_ed25519"
_CONFIG_BEGIN = "# >>> gitgo (managed, do not edit) >>>"
_CONFIG_END = "# <<< gitgo (managed) <<<"


def get_ssh_key_path():
    """GitGo's own key. It never touches ~/.ssh/id_ed25519."""
    return Path.home() / ".ssh" / GITGO_KEY_NAME


def get_legacy_key_path():
    return Path.home() / ".ssh" / LEGACY_KEY_NAME


def _signing_key_setting() -> str:
    try:
        return run_command(["git", "config", "--global", "user.signingkey"]).strip()
    except GitCommandError:
        return ""


def migrate_legacy_key() -> bool:
    """Adopt an id_ed25519 key that older GitGo versions created.

    Older versions generated ~/.ssh/id_ed25519 and pointed user.signingkey at it.
    We only treat the key as GitGo's when that setting still names it. The key is
    COPIED, never moved, so anything else that uses id_ed25519 keeps working, and
    GitHub already knows the key, so no re-registration is needed.
    Returns True when a migration happened.
    """
    new, old = get_ssh_key_path(), get_legacy_key_path()
    if new.exists() or not old.exists():
        return False
    setting = _signing_key_setting()
    if not setting:
        return False
    try:
        if Path(setting).expanduser().resolve() != old.resolve():
            return False
    except OSError:
        return False

    try:
        shutil.copy2(old, new)
        old_pub = old.with_name(old.name + ".pub")
        if old_pub.exists():
            shutil.copy2(old_pub, new.with_name(new.name + ".pub"))
        if os.name != "nt":
            os.chmod(new, 0o600)
    except OSError as e:
        warning(f"Could not copy your existing GitGo key to {new}: {e}")
        return False

    try:
        run_command(["git", "config", "--global", "user.signingkey", str(new)])
    except GitCommandError:
        pass
    ensure_ssh_config(new)
    ensure_ssh_agent(new, quiet=True)
    success(f"GitGo now uses its own key: {new}")
    info(f"Your original {old} was copied, not moved, and is untouched.")
    return True


def _config_block(key_path: Path) -> str:
    key = str(key_path).replace("\\", "/")
    return (
        f"{_CONFIG_BEGIN}\n"
        "Host github.com\n"
        f'    IdentityFile "{key}"\n'
        f"{_CONFIG_END}\n"
    )


def _strip_config_block(text: str) -> str:
    if _CONFIG_BEGIN not in text:
        return text
    before, _, rest = text.partition(_CONFIG_BEGIN)
    _, _, after = rest.partition(_CONFIG_END)
    return before + after.lstrip("\n")


def ensure_ssh_config(key_path: Path):
    """Make github.com use GitGo's key, in a marked block at the top of ~/.ssh/config.

    ssh uses the first value it finds, so the block goes first. Everything outside
    the markers is left exactly as it was, and re-running replaces only our block.
    """
    config = Path.home() / ".ssh" / "config"
    config.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = config.read_text() if config.exists() else ""
        body = _strip_config_block(existing)
        config.write_text(_config_block(key_path) + ("\n" + body if body.strip() else ""))
        if os.name != "nt":
            os.chmod(config, 0o600)
    except OSError as e:
        warning(f"Could not update {config}: {e}")


def remove_ssh_config_block():
    config = Path.home() / ".ssh" / "config"
    try:
        if not config.exists():
            return
        text = config.read_text()
        if _CONFIG_BEGIN in text:
            config.write_text(_strip_config_block(text))
    except OSError:
        pass


def is_agent_loaded(key_path: Path) -> bool:
    """Return True if the given key is currently loaded in the SSH agent."""
    try:
        result = subprocess.run(
            ["ssh-add", "-l"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout:
            # Check by key file path or by fingerprint presence.
            key_str = str(key_path)
            return key_str in result.stdout
        return False
    except Exception:
        return False


def generate_ssh_key(email):
    if not email or "@" not in email or "." not in email:
        raise GitGoError("Invalid email address provided for SSH key generation.")

    key_path = get_ssh_key_path()
    if not key_path.parent.exists():
        key_path.parent.mkdir(parents=True)

    if key_path.exists():
        from pygitgo.utils.cli_io import confirm
        if not confirm(f"SSH key {key_path} already exists. Overwrite it? (y/n): ", destructive=True):
            raise GitGoError("SSH key generation canceled. Back up your existing key or configure it manually.")
        os.remove(key_path)
    if (key_path.parent / f"{key_path.name}.pub").exists():
        os.remove(key_path.parent / f"{key_path.name}.pub")

    command = [
        "ssh-keygen",
        "-t", "ed25519",
        "-C", email,
        "-f", str(key_path),
        "-N", ""
    ]

    try:
        run_command(command=command)
    except GitCommandError as e:
        raise GitGoError(
            "\nFailed to generate SSH key. Is 'ssh-keygen' installed?\n"
            f"Details: {e}"
        )

    ensure_ssh_config(key_path)
    ensure_ssh_agent(key_path, quiet=True)

    return key_path


def convert_https_to_ssh(url: str) -> Optional[str]:
    """Convert an HTTPS remote URL to SSH format. Works for any hostname."""
    url = url.strip()
    # Match https://host/owner/repo or https://host/owner/repo.git
    pattern = r"^https?://([^/]+)/([^/]+)/([^/]+?)(?:\.git)?/?$"
    match = re.match(pattern, url)
    if match:
        host = match.group(1)
        owner = match.group(2)
        repo = match.group(3)
        return f"git@{host}:{owner}/{repo}.git"
    return None


def is_ssh_url(url):
    return url.strip().startswith("git@")


def _try_ssh_add(key_path):
    try:
        run_command(["ssh-add", str(key_path)])
        return True
    except (GitCommandError, OSError):
        return False


def ensure_ssh_agent(key_path, quiet=False):
    if _try_ssh_add(key_path):
        return True

    if get_platform() == "windows":
        try:
            subprocess.run(
                ["sc", "start", "ssh-agent"],
                capture_output=True, timeout=5
            )
        except Exception:
            pass

        time.sleep(1)

        if _try_ssh_add(key_path):
            return True

        if not quiet:
            warning("SSH agent is not running. Key may not persist across sessions.")
            info("To fix this, run PowerShell as Administrator and type:")
            info("  Set-Service ssh-agent -StartupType Automatic")
            info("  Start-Service ssh-agent")
            info("Then run 'gitgo user login' again.")

    else:
        if not quiet:
            warning("SSH agent is not running. Key may not persist across sessions.")
            info("Run:  eval $(ssh-agent) && ssh-add")

    return False
