from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.colors import info, success, warning
from pygitgo.utils.platform import get_platform
from pygitgo.utils.executor import run_command
from pathlib import Path
import subprocess
import time
import os
import re


SSH_TIMEOUT_SECONDS = 10

_cached_ssh_response = None
_cache_populated = False


def ensure_github_known_host():
    known_hosts = Path.home() / ".ssh" / "known_hosts"
    known_hosts.parent.mkdir(parents=True, exist_ok=True)

    try:
        if known_hosts.exists():
            with open(known_hosts, "r") as f:
                if "github.com" in f.read():
                    return 
    except Exception:
        pass

    info("Adding GitHub to known_hosts...")
    try:
        result = run_command(["ssh-keyscan", "-H", "github.com"], return_complete=True)
    
        if result.stdout and "github.com" in result.stdout:
            with open(known_hosts, "a") as f:
                f.write(result.stdout)
                if not result.stdout.endswith("\n"):
                    f.write("\n")
            success("GitHub added to known_hosts.")
    except GitCommandError:
        warning("Could not automatically add GitHub to known_hosts. You might be prompted.")


def _get_github_ssh_response():
    try:
        result = subprocess.run(
            ["ssh", "-T", "-o", "BatchMode=yes", "git@github.com"],
            capture_output=True, text=True,
            timeout=SSH_TIMEOUT_SECONDS, stdin=subprocess.DEVNULL,
        )
        return (result.stderr or "") + (result.stdout or "")
    except (subprocess.TimeoutExpired, OSError):
        return None


def _get_cached_ssh_response():
    global _cached_ssh_response, _cache_populated
    if not _cache_populated:
        _cached_ssh_response = _get_github_ssh_response()
        _cache_populated = True
    return _cached_ssh_response


def clear_ssh_cache():
    global _cached_ssh_response, _cache_populated
    _cached_ssh_response = None
    _cache_populated = False


def check_connection(ok_text=None, fail_text=None):
    from yaspin import yaspin
    import sys
    
    ensure_github_known_host()

    kwargs = {"text": ok_text or "Verifying GitHub connection..."}
    if sys.stdout.isatty():
        kwargs["color"] = "cyan"
    spinner = yaspin(**kwargs)
    spinner.start()

    output = _get_cached_ssh_response()
    connected = output is not None and "successfully authenticated" in output

    if connected:
        if ok_text:
            spinner.text = ok_text
        spinner.ok("✔")
    else:
        if fail_text:
            spinner.text = fail_text
        spinner.fail("✖")

    return connected


def get_github_username():
    output = _get_cached_ssh_response()
    if output and "Hi " in output and "!" in output:
        try:
            return output.split("Hi ")[1].split("!")[0]
        except (IndexError, ValueError):
            pass
    return None

def get_ssh_key_path():
    return Path.home() / ".ssh" / "id_ed25519"

def generate_ssh_key(email):
    if not email or "@" not in email or "." not in email:
        raise GitGoError("Invalid email address provided for SSH key generation.")
    
    key_path = get_ssh_key_path()
    if not key_path.parent.exists():
        key_path.parent.mkdir(parents=True)
    
    if key_path.exists():
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
            "\nFailed to generate SSH key. Is 'ssh-keygen' installed on your system?\n"
            f"Details: {e}"
        )
    
    ensure_ssh_agent(key_path)
    
    return key_path


def convert_https_to_ssh(url):    
    pattern = r'^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
    match = re.match(pattern, url.strip())
    
    if match:
        owner = match.group(1)
        repo = match.group(2)
        return f"git@github.com:{owner}/{repo}.git"
    
    return None


def is_ssh_url(url):
    return url.strip().startswith("git@")

def _try_ssh_add(key_path):
    try:
        run_command(["ssh-add", str(key_path)])
        return True
    except (GitCommandError, OSError):
        return False

def ensure_ssh_agent(key_path):
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
        
        warning("SSH agent is not running on this machine.")
        info("To fix this permanently, run in PowerShell (as Administrator):")
        info("  Set-Service ssh-agent -StartupType Automatic")
        info("  Start-Service ssh-agent")
        info("Then run 'gitgo user login' again.")

    else:
        warning("SSH agent is not running.")
        info("Run:  eval $(ssh-agent) && ssh-add")
        info("Then run 'gitgo user login' again.")

    return False
    
