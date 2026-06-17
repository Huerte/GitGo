from pygitgo.auth.ssh_utils import convert_https_to_ssh, get_ssh_key_path, is_ssh_url, check_connection
from pygitgo.exceptions import GitGoError, GitCommandError
from pygitgo.auth.account import sanitize_signing_config
from pygitgo.commands.git_remote import handle_rebase
from pygitgo.utils.config import get_default_branch
from pygitgo.utils.executor import run_command
from pygitgo.utils.cli_io import info, warning
import os



def _get_signing_flags():
    key_path = get_ssh_key_path()
    if not key_path.exists():
        return []
    return [
        "-c", "gpg.format=ssh",
        "-c", f"user.signingkey={key_path}",
    ]


def git_commit(commit_message, loading_msg="Committing changes...", skip_staging=False, ok_text=None):
    if not ok_text:
        ok_text = "Changes committed."
    try:
        status_result = run_command(["git", "status", "--porcelain"])
        if not status_result.strip():
            return False
    except GitCommandError:
        return False
    
    sanitize_signing_config()

    if not skip_staging:
        run_command(["git", "add", "."], loading_msg="Staging files...", ok_text="Files staged.")

    clean_message = commit_message.strip('"\'')

    signing_flags = _get_signing_flags()
    commit_command = ["git"] + signing_flags + ["commit", "-S", "-m", clean_message]
    run_command(commit_command, loading_msg=loading_msg, ok_text=ok_text)

    return True


def git_init(ok_text=None):
    if os.path.isdir(".git"):
        warning("Already a git repository! Skipping init...")
        return False

    default_main_branch = get_default_branch()

    if not ok_text:
        ok_text = "Git repository initialized."

    try:
        run_command(["git", "init", "-b", default_main_branch], loading_msg="Initializing git repository...", ok_text=ok_text)
    except GitCommandError:
        run_command(["git", "init"], loading_msg="Initializing git repository...")
        run_command(["git", "checkout", "-b", default_main_branch], ok_text=ok_text)

    return True


def git_push(branch, ok_text=None):
    if not ok_text:
        ok_text = f"Pushed to remote branch '{branch}'."
    try:
        remote_url = run_command(["git", "remote", "get-url", "origin"]).strip()
    except GitCommandError:
        remote_url = None

    if remote_url and not is_ssh_url(remote_url) and check_connection():
        ssh_url = convert_https_to_ssh(remote_url)
        if ssh_url:
            run_command(["git", "remote", "set-url", "origin", ssh_url], loading_msg="Converting remote from HTTPS to SSH for secure push...", ok_text=f"Remote updated to: {ssh_url}")

    try:
        run_command(["git", "push", "-u", "origin", branch], loading_msg=f"Pushing to remote branch '{branch}'...", ok_text=ok_text, err_text="Push failed: verify your remote URL and SSH key, then try again.")
    except (GitCommandError, OSError) as e:
        info("Run:  git remote -v   to inspect your current remote.")
        if "rebase in progress" in str(e):
            handle_rebase()
        else:
            raise GitGoError("Push failed - see above.")
