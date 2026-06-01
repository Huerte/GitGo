from pygitgo.auth.ssh_utils import convert_https_to_ssh, get_ssh_key_path, is_ssh_url, check_connection
from pygitgo.utils.colors import info, success, warning, error
from pygitgo.exceptions import GitGoError, GitCommandError
from pygitgo.utils.executor import run_command
from pygitgo.utils.config import get_config
from argparse import Namespace
import os


def get_status_content():
    try:
        status = run_command(["git", "status", "--porcelain"])
        if not status.strip():
            raise GitGoError("Working tree is clean. Nothing to commit.")
        return status
    except GitCommandError:
        raise GitGoError("Working tree is clean. Nothing to commit.")
    

def get_current_branch():
    branch = run_command(["git", "branch", "--show-current"]).strip()
    if not branch:
        branch = run_command(["git", "rev-parse", "--short", "HEAD"]).strip()
    return branch

def get_main_branch():
    default_main_branch = get_config("default-branch", "main")

    try:
        output = run_command(['git', 'remote', 'show', 'origin'])
    except GitCommandError:
        return default_main_branch

    if "HEAD branch:" not in output:
        return default_main_branch

    return output.split("HEAD branch:")[-1].strip().splitlines()[0].strip()

def is_branch_exist(branch):
    return bool(run_command(["git", "branch", "-r", "--list", f"*/{branch}"])) or bool(run_command(["git", "branch", "--list", branch]))


def git_new_branch(branch):
    try:
        run_command(["git", "checkout", "-b", branch], loading_msg=f"Creating branch '{branch}'...")
        print()
        success(f"Branch '{branch}' created.")
    except GitCommandError:
        error(f"Failed to create branch '{branch}'! It may already exist.")
        choice = input("\nWould you like to jump to the existing branch instead? (y/n): ").strip().lower()
        if choice == "y":
            from pygitgo.commands.jump import jump_operation 
            jump_operation(Namespace(branch=branch))
        else:
            raise GitGoError(f"Operation canceled. Branch '{branch}' already exists.")
        
    return branch


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

    default_main_branch = get_config("default-branch", "main")

    try:
        run_command(["git", "init", "-b", default_main_branch], loading_msg="Initializing git repository...")
    except GitCommandError:
        run_command(["git", "init"], loading_msg="Initializing git repository...")
        run_command(["git", "checkout", "-b", default_main_branch])

    success("Git repository initialized.")
    return True


def add_remote_origin(repo_url):
    clean_url = repo_url.strip('"\'')

    try:
        existing_remote = run_command(["git", "remote", "get-url", "origin"])
        warning(f"Remote origin already exists: {existing_remote}")
        run_command(["git", "remote", "set-url", "origin", clean_url], loading_msg="Updating remote URL...")
    except GitCommandError:
        run_command(["git", "remote", "add", "origin", clean_url], loading_msg="Adding remote origin...")

    success(f"Remote origin set to: {clean_url}")


def confirm_remote_link():
    try:
        run_command(["git", "ls-remote", "origin"], loading_msg="Testing connection to remote...")
        success("Remote is reachable.")
        return True
    except GitCommandError:
        error("Connection failed — verify the URL and your SSH key.")
        info("Run:  git remote -v   to inspect your current remote.")
        return False


def create_main_branch():
    try:
        current_branch = run_command(["git", "branch", "--show-current"])
    except GitCommandError:
        current_branch = None

    if not current_branch or not current_branch.strip():
        run_command(["git", "checkout", "-b", "main"], loading_msg="Setting default branch to 'main'...")
    elif current_branch.strip() != "main":
        run_command(["git", "branch", "-m", "main"], loading_msg=f"Renaming branch '{current_branch.strip()}' to 'main'...")
    else:
        success("Already on 'main' branch.")


def check_and_sync_branch(branch):
    try:
        run_command(["git", "fetch", "origin"], loading_msg="Checking if branch is up to date...")

        try:
            local_commit = run_command(["git", "rev-parse", branch])
            remote_commit = run_command(["git", "rev-parse", f"origin/{branch}"])

            if local_commit != remote_commit:
                behind_check = run_command(
                    ["git", "rev-list", "--count", f"{branch}..origin/{branch}"]
                )
                if behind_check and int(behind_check) > 0:
                    warning(f"Local branch is behind remote by {behind_check} commit(s). Pulling changes...")
                    output = run_command(["git", "pull", "--rebase", "origin", branch], loading_msg="Pulling changes from remote...")
                    if output:
                        print(output)
                    success("Synced with remote.")
                else:
                    success("Branch is up to date.")
            else:
                success("Branch is already up to date.")
        except (GitCommandError, ValueError):
            warning("Remote branch doesn't exist yet. First push will create it.")
    except (GitCommandError, OSError):
        warning("Could not fetch from remote. Proceeding with push...")


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


def handle_rebase():
    warning("Conflict detected during rebase.")
    info("Resolve conflicts manually, then run:")
    info("    git add <files>")
    info("    git rebase --continue")
    info("When finished, run 'gitgo push <branch> <message>' again.")
    raise GitGoError("Push aborted — rebase conflict in progress.")

    
