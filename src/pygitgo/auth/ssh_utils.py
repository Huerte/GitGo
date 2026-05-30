from pygitgo.utils.colors import info, success, warning, error
from pygitgo.utils.executor import run_command
from pygitgo.utils import platform_utils
from pathlib import Path
import subprocess
import sys
import os

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
    result = run_command(["ssh-keyscan", "-H", "github.com"], allow_fail=True, return_complete=True)
    
    if not isinstance(result, Exception) and result.stdout and "github.com" in result.stdout:
        with open(known_hosts, "a") as f:
            f.write(result.stdout)
            if not result.stdout.endswith("\n"):
                f.write("\n")
        success("GitHub added to known_hosts.")
    else:
        warning("Could not automatically add GitHub to known_hosts. You might be prompted.")

def check_connection():
    ensure_github_known_host()
    try:
        result = subprocess.run(
            ["ssh", "-T", "-o", "BatchMode=yes", "git@github.com"],
            capture_output=True,
            text=True,
            timeout=SSH_TIMEOUT_SECONDS,
            stdin=subprocess.DEVNULL,
        )
        output = (result.stderr or "") + (result.stdout or "")
        return "successfully authenticated" in output
    except (subprocess.TimeoutExpired, OSError):
        return False

def get_github_username():
    try:
        result = subprocess.run(
            ["ssh", "-T", "-o", "BatchMode=yes", "git@github.com"],
            capture_output=True,
            text=True,
            timeout=SSH_TIMEOUT_SECONDS,
            stdin=subprocess.DEVNULL,
        )
        output = (result.stderr or "") + (result.stdout or "")

        if "Hi " in output and "!" in output:
            try:
                return output.split("Hi ")[1].split("!")[0]
            except (IndexError, ValueError):
                return None
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None

def get_ssh_key_path():
    return Path.home() / ".ssh" / "id_ed25519"

def generate_ssh_key(email):
    if not email or "@" not in email or "." not in email:
        error("Invalid email address provided for SSH key generation.")
        return 
    
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
    run_command(command=command)

    try:
        run_command(["ssh-add", str(key_path)], allow_fail=True)
    except (subprocess.CalledProcessError, OSError):
        pass 
    
    return key_path

def open_github_settings():
    url = "https://github.com/settings/ssh/new"
    opened = False

    try:
        if platform_utils.is_windows():
            os.system(f"start {url}")
            opened = True
        elif platform_utils.is_termux():
            os.system(f"termux-open {url}")
            opened = True
        elif platform_utils.is_linux() or platform_utils.is_macos():
            exit_code = os.system(f"xdg-open {url} 2>/dev/null")
            opened = exit_code == 0
        else:
            import webbrowser
            webbrowser.open(url)
            opened = True
    except Exception:
        opened = False

    if not opened:
        warning("Could not open browser automatically.")

    info(f"\nIf the browser did not open, visit this URL manually:")
    print(f"\n  {url}\n")


def convert_https_to_ssh(url):

    import re
    
    pattern = r'^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
    match = re.match(pattern, url.strip())
    
    if match:
        owner = match.group(1)
        repo = match.group(2)
        return f"git@github.com:{owner}/{repo}.git"
    
    return None


def is_ssh_url(url):
    return url.strip().startswith("git@")
