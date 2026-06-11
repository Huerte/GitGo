from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.colors import info, success, warning
from pygitgo.utils.executor import run_command
from pathlib import Path
import subprocess
import os
import re


SSH_TIMEOUT_SECONDS = 10


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

def check_connection():
    ensure_github_known_host()
    output = _get_github_ssh_response()
    return output is not None and "successfully authenticated" in output

def get_github_username():
    output = _get_github_ssh_response()
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
    try:
        run_command(["ssh-add", str(key_path)])
    except (GitCommandError, OSError):
        pass 
    
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
