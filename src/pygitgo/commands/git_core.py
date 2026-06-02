from pygitgo.auth.ssh_utils import convert_https_to_ssh, get_ssh_key_path, is_ssh_url, check_connection
from pygitgo.utils.colors import info, success, warning, error
from pygitgo.exceptions import GitGoError, GitCommandError
from pygitgo.commands.git_remote import handle_rebase
from pygitgo.utils.config import get_default_branch
from pygitgo.utils.executor import run_command
import os



def _get_signing_flags():
    key_path = get_ssh_key_path()
    if not key_path.exists():
        return []
    return [
        "-c", "gpg.format=ssh",
        "-c", f"user.signingkey={key_path}",
    ]


def git_commit(commit_message, loading_msg="Commiting changes...", skip_staging=False):
    try:
        status_result = run_command(["git", "status", "--porcelain"])
        if not status_result.strip():
            return False
    except GitCommandError:
        return False

    if not skip_staging:
        run_command(["git", "add", "."], loading_msg="Staging files...")

    clean_message = commit_message.strip('"\'')

    signing_flags = _get_signing_flags()
    commit_command = ["git"] + signing_flags + ["commit", "-S", "-m", clean_message]
    run_command(commit_command, loading_msg=loading_msg)

    return True


def git_init():
    if os.path.isdir(".git"):
        warning("Already a git repository! Skipping init...")
        return False

    default_main_branch = get_default_branch()

    try:
        run_command(["git", "init", "-b", default_main_branch], loading_msg="Initializing git repository...")
    except GitCommandError:
        run_command(["git", "init"], loading_msg="Initializing git repository...")
        run_command(["git", "checkout", "-b", default_main_branch])

    success("Git repository initialized.")
    return True


def git_push(branch):
    try:
        remote_url = run_command(["git", "remote", "get-url", "origin"]).strip()
    except GitCommandError:
        remote_url = None

    if remote_url and not is_ssh_url(remote_url) and check_connection():
        ssh_url = convert_https_to_ssh(remote_url)
        if ssh_url:
            run_command(["git", "remote", "set-url", "origin", ssh_url], loading_msg="Converting remote from HTTPS to SSH for secure push...")
            success(f"Remote updated to: {ssh_url}")

    try:
        run_command(["git", "push", "-u", "origin", branch], loading_msg=f"Pushing to remote branch '{branch}'...")
    except (GitCommandError, OSError) as e:
        error("Push failed — verify your remote URL and SSH key, then try again.")
        info("Run:  git remote -v   to inspect your current remote.")
        if "rebase in progress" in str(e):
            handle_rebase()
        else:
            raise GitGoError("Push failed - see above.")
