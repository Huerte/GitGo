from pygitgo.utils.cli_io import info, success, warning, error, write, confirm
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.platform import get_platform
from pygitgo.utils.executor import run_command
from pygitgo.utils.platform import open_url, copy_to_clipboard
from .account import get_user
from . import ssh_utils
import shutil
import time
import sys
import os



def _configure_ssh_signing(key_path):
    try:
        run_command(["git", "config", "--global", "gpg.format", "ssh"])
        run_command(["git", "config", "--global", "user.signingkey", str(key_path)])
    except Exception:
        pass
    

def _hostname_label():
    import socket
    try:
        return socket.gethostname() or "computer"
    except OSError:
        return "computer"


def _device_login():
    """Browser-based login: approve a code on GitHub, and GitGo registers the key itself.

    Returns True on success. Returns None when the flow could not complete and the
    caller should fall back to the manual copy/paste steps.
    """
    from . import device_flow
    from .account import ensure_user_configure

    try:
        device = device_flow.start()
        code, url = device["user_code"], device["verification_uri"]

        write(required=True)
        write(f"  Your code:  {code}", required=True)
        write(f"  Open:       {url}", required=True)
        write(required=True)
        if copy_to_clipboard(code):
            success("The code was copied to your clipboard.", required=True)
        input("Press Enter to open GitHub, then paste the code and approve...")
        open_url(url)
        info("Waiting for you to approve on GitHub... (Ctrl+C to cancel)", required=True)

        token = device_flow.wait_for_token(device)
        username, email = device_flow.fetch_identity(token)
        success(f"Authorized as {username}.", required=True)

        key_path = ssh_utils.generate_ssh_key(email=email)
        pub_key = open(str(key_path) + ".pub", "r").read().strip()
        device_flow.upload_keys(token, pub_key, f"GitGo ({_hostname_label()})")
        success("SSH key added to your GitHub account (login + verified commits).", required=True)
    except device_flow.DeviceFlowError as e:
        warning(f"Browser login did not finish: {e}", required=True)
        info("Falling back to the manual steps.", required=True)
        return None
    except GitGoError as e:
        error(str(e))
        return False

    ssh_utils.clear_ssh_cache()
    if ssh_utils.check_connection(ok_text="Login successful. You are connected.", fail_text="SSH key not recognised by GitHub."):
        _configure_ssh_signing(key_path)
        ensure_user_configure(default_email=email, default_username=username)
        return True
    return None


def login():
    from .account import sanitize_signing_config, ensure_user_configure

    sanitize_signing_config()  # also adopts a key made by older GitGo versions

    key_path = ssh_utils.get_ssh_key_path()
    already_logged_in = key_path.exists()
    ok_text = "Already logged in via GitGo." if already_logged_in else "GitHub connection verified."

    if ssh_utils.check_connection(ok_text=ok_text, fail_text="Not connected to GitHub."):
        if already_logged_in:
            _configure_ssh_signing(key_path)
            ensure_user_configure(default_username=ssh_utils.get_github_username())
            return True

        info("GitHub already accepts one of your existing SSH keys, so pushing works.", required=True)
        info("GitGo can add its own key next to it (yours is not touched) to get Verified commits.", required=True)
        if not confirm("Set up GitGo's key for Verified commits? (y/n): "):
            info("Skipped. Run 'gitgo user login' any time to add it.", required=True)
            return True
    else:
        info("Initiating login sequence...", required=True)

    from . import device_flow
    if device_flow.is_available() and sys.stdin.isatty():
        result = _device_login()
        if result is not None:
            return result

    return _manual_login()


def _manual_login():
    from .account import ensure_user_configure

    while True:
        email = input("Enter your email for GitHub: ").strip()
        if "@" in email and "." in email:
            break
        else:
            error("Please enter a valid email address.")

    try:
        key_path = ssh_utils.generate_ssh_key(email=email)
    except GitGoError as e:
        error(str(e))
        return False

    pub_key_path = str(key_path) + ".pub"

    with open(pub_key_path, "r") as f:
        pub_key = f.read()

    if not pub_key:
        error("Failed to read the generated public key.")
        return False

    success("SSH Key generated successfully!", required=True)

    write(required=True)
    write("  Your SSH public key:", required=True)
    write(required=True)
    write(f"  {pub_key.strip()}", required=True)
    write(required=True)

    info("Copy the key above, then add it TWICE on GitHub:", required=True)
    info("  1. Authentication Key  (for pushing and pulling)", required=True)
    info("  2. Signing Key         (for Verified commits)", required=True)
    info("Same key text for both entries.", required=True)

    if copy_to_clipboard(pub_key.strip()):
        success("The key was copied to your clipboard.", required=True)
        input("\nPress Enter to open GitHub, then paste it in the Key box...")
    else:
        input("\nOnce you've copied the key, press Enter to open GitHub...")

    open_url("https://github.com/settings/ssh/new")

    input(
        "\nAfter adding both keys on GitHub,\n"
        "come back here and press Enter to verify the connection..."
    )

    ssh_utils.clear_ssh_cache()

    if ssh_utils.check_connection(ok_text="Login successful. You are connected.", fail_text="SSH key not recognised by GitHub."):
        github_username = ssh_utils.get_github_username()
        ensure_user_configure(default_email=email, default_username=github_username)
        return True

    raw_output, timed_out, os_error = ssh_utils._get_cached_ssh_response()
    cause = ssh_utils.classify_connection_error(raw_output, timed_out, os_error)

    error("Login failed. GitHub did not accept the SSH key.")
    info(f"Reason: {cause}", required=True)

    if get_platform() == "windows" and not timed_out:
        info("", required=True)
        info("If the key was added correctly but still fails, the SSH agent may not be running.", required=True)
        info("Fix (run PowerShell as Administrator):", required=True)
        info("  Set-Service ssh-agent -StartupType Automatic", required=True)
        info("  Start-Service ssh-agent", required=True)
        info("Then run 'gitgo user login' again.", required=True)

    info("", required=True)
    info("Full guide: https://github.com/Huerte/GitGo/blob/main/docs/login-guide.md", required=True)
    return False


def _backup_key(key_path):
    """Move the key pair aside instead of deleting it. Returns the private-key backup path."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup = key_path.with_name(f"{key_path.name}.gitgo-backup-{stamp}")
    shutil.move(str(key_path), str(backup))

    pub = key_path.with_name(key_path.name + ".pub")
    if pub.exists():
        shutil.move(str(pub), str(backup) + ".pub")
    return backup


def logout(clear_identity=None):
    key_path = ssh_utils.get_ssh_key_path()
    if not key_path.exists():
        warning("You are already logged out (no keys found).")
        return False

    warning(f"This will remove GitGo's SSH key at {key_path}.")
    info("Your own keys (for example ~/.ssh/id_ed25519) are not touched.")
    info("GitGo keeps a backup copy next to it, so you can restore it by renaming the file.")
    info("The key is NOT removed from your GitHub account. Do that at github.com/settings/keys.")
    if not confirm("Remove this SSH key? (y/n): ", destructive=True):
        info("Canceled. Nothing was changed.")
        return False

    try:
        backup = _backup_key(key_path)
        ssh_utils.remove_ssh_config_block()
        success(f"SSH key removed. Backup saved at: {backup}")
    except Exception as e:
        error(f"Failed to remove SSH keys\nCAUSE OF ERROR: {e}")
        return False

    name, email = get_user()
    if name or email:
        if clear_identity is None:
            clear_identity = confirm(f"Also clear your global Git identity ({name} <{email}>)? (y/n): ")
        if clear_identity:
            for key, label in (("user.name", "username"), ("user.email", "email")):
                try:
                    run_command(["git", "config", "--global", "--unset-all", key], loading_msg=f"Clearing Git {label}...", ok_text=f"Git {label} cleared.")
                except GitCommandError:
                    pass
        else:
            info("Git identity left as it was.")

    success("User successfully logged out.")
    return True
