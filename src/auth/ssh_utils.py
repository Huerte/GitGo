from utils.executor import run_command
from utils.colors import *
from pathlib import Path
import sys
import os



def ensure_github_known_host():
    # Make sure github.com is in the known_hosts file to avoid authenticity prompts.
    known_hosts = Path.home() / ".ssh" / "known_hosts"
    known_hosts.parent.mkdir(parents=True, exist_ok=True)

    # Only add if github.com is not already there
    try:
        if known_hosts.exists():
            with open(known_hosts, "r") as f:
                if "github.com" in f.read():
                    return 
    except Exception:
        pass

    info("Adding GitHub to known_hosts...")
    result = run_command(["ssh-keyscan", "-H", "github.com"], allow_fail=True, return_complete=True)
    
    # Check if command succeeded and has output
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
    result = run_command(["ssh", "-T", "git@github.com"], allow_fail=True, return_complete=True)
    return "successfully authenticated" in result.stderr

def get_github_username():

    result = run_command(["ssh", "-T", "git@github.com"], allow_fail=True, return_complete=True)
    output = result.stderr
    
    if "Hi " in output and "!" in output:
        try:
            username = output.split("Hi ")[1].split("!")[0]
            return username
        except:
            return None
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
    except:
        pass 
    
    return key_path

def open_github_settings():
    url = "https://github.com/settings/ssh/new"
    if sys.platform.startswith("win"):
        # Windows
        os.system(f"start {url}")
    elif "TERMUX_VERSION" in os.environ:
        # Termux app | ADDED FOR MY OWN USE
        os.system(f"termux-open {url}")
    else:
        # Linux / Mac
        os.system(f"xdg-open {url}")
