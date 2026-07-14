from pygitgo.utils.cli_io import info, success, warning, error, write
from pygitgo.utils.platform import get_platform
from pygitgo.utils.executor import run_command
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.platform import open_url
from . import ssh_utils
import os



def _configure_ssh_signing(key_path):
    try:
        run_command(["git", "config", "--global", "gpg.format", "ssh"])
        run_command(["git", "config", "--global", "user.signingkey", str(key_path)])
    except Exception:
        pass
    

def login():
    from .account import sanitize_signing_config, ensure_user_configure

    sanitize_signing_config()

    key_path = ssh_utils.get_ssh_key_path()
    already_logged_in = key_path.exists()
    ok_text = "Already logged in via GitGo." if already_logged_in else "GitHub connection verified."

    if ssh_utils.check_connection(ok_text=ok_text, fail_text="Not connected to GitHub."):
        if already_logged_in:
            _configure_ssh_signing(key_path)
            ensure_user_configure(default_username=ssh_utils.get_github_username())
        else:
            warning("GitHub SSH connection is active, but NOT via a GitGo-managed key.")
            warning("To use GitGo's full login (SSH + verified commits), you must log out first.")
            info("Run: gitgo user logout")
            info("Then run: gitgo user login")

        return True
    
    info("Initiating login sequence...")
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

    success("SSH Key generated successfully!")

    write()
    write("  Your SSH public key:")
    write()
    write(f"  {pub_key.strip()}")
    write()

    info("Copy the key above, then add it TWICE on GitHub:")
    info("  1. Authentication Key  (for pushing and pulling)")
    info("  2. Signing Key         (for Verified commits)")
    info("Same key text for both entries.")

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
    info(f"Reason: {cause}")

    if get_platform() == "windows" and not timed_out:
        info("")
        info("If the key was added correctly but still fails, the SSH agent may not be running.")
        info("Fix (run PowerShell as Administrator):")
        info("  Set-Service ssh-agent -StartupType Automatic")
        info("  Start-Service ssh-agent")
        info("Then run 'gitgo user login' again.")

    info("")
    info("Full guide: https://github.com/Huerte/GitGo/blob/main/docs/login-guide.md")
    return False

 
def logout():
    key_path = ssh_utils.get_ssh_key_path()
    if not key_path.exists():
        warning("You are already logged out (no keys found).")
        return False
    
    try:
        
        os.remove(key_path)

        pub_key_path = str(key_path) + ".pub"
        if os.path.exists(pub_key_path):
            os.remove(pub_key_path)

        try:
            run_command(["git", "config", "--global", "--unset-all", "user.name"], loading_msg="Clearing Git username...", ok_text="Git username cleared.")
        except GitCommandError:
            pass
        
        try:
            run_command(["git", "config", "--global", "--unset-all", "user.email"], loading_msg="Clearing Git email...", ok_text="Git email cleared.")
        except GitCommandError:
            pass

        success("User successfully logged out.")
        return True
    
    except Exception as e:
        error(f"Failed to remove SSH keys\nCAUSE OF ERROR: {e}")
        return False
