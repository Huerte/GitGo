from utils.executor import run_command
from utils.colors import *
from pathlib import Path
import sys
import os


def check_connection():
    result = run_command(["ssh", "-T", "git@github.com"], allow_fail=True, return_complete=True)
    return "successfully authenticated" in result.stderr

def get_ssh_key_path():
    return Path.home() / ".ssh" / "id_ed25519"

def generate_ssh_key(email):
    if not email or "@" not in email or "." not in email:
        error("Invalid email address provided for SSH key generation.")
        return 
    
    key_path = get_ssh_key_path()
    if not key_path.parent.exists():
        key_path.parent.mkdir(parents=True)

    command = [
        "ssh-keygen",
        "-t", "ed25519",
        "-C", email,
        "-f", str(key_path),
        "-N", ""
    ]
    run_command(command=command)

    # Add to connection agent
    run_command(["ssh-add", str(key_path)], allow_fail=True)
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
