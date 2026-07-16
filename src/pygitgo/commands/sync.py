from pygitgo.commands.git_core import git_commit, git_push, ensure_inside_git_repository
from pygitgo.utils.cli_io import info, error, warning, banner, write
from pygitgo.commands.git_branch import get_current_branch
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.commands.pull import _pull_interrupt_cleanup
from pygitgo.utils.executor import run_command
from pygitgo.utils.config import get_config
import sys


def sync_operation(args):
    ensure_inside_git_repository()

    message = getattr(args, 'message', None)
    try:
        branch = get_current_branch(safe=True)
    except GitCommandError as e:
        raise GitGoError(f"Could not determine current branch: {e}")

    info(f"Starting sync process for branch '{branch}'...")

    remote_exists = True
    try:
        run_command(["git", "ls-remote", "--exit-code", "--heads", "origin", branch])
    except GitCommandError:
        remote_exists = False
        info(f"Branch '{branch}' does not exist on the remote yet.")

    if remote_exists:
        try:
            run_command(
                ["git", "pull", "--rebase", "--autostash", "origin", branch],
                loading_msg=f"Downloading latest updates for '{branch}'...",
                ok_text="Successfully pulled latest changes."   
            )
        except KeyboardInterrupt:
            write()
            warning("Sync interrupted (Ctrl+C).")
            _pull_interrupt_cleanup()
            sys.exit(130)
        except GitCommandError as e:
            error_msg = getattr(e, 'stderr', str(e)).lower()
            if "conflict" in error_msg or "rebase in progress" in error_msg:
                error("MERGE CONFLICT DETECTED DURING PULL!")
                write()
                info("Fix the conflicts in your editor, then run 'gitgo resolve'.", required=True)
                raise GitGoError("Sync paused — resolve conflicts to continue.")
            else:
                raise GitGoError(f"Failed to pull from remote: {e}")

    if not message:
        message = get_config("default-message", "chore: new changes applied")
        info(f"No commit message provided. Using default: '{message}'\n")

    if git_commit(message):
        git_push(branch)    
    else:
        try:
            if remote_exists:
                unpushed = run_command(["git", "log", "--oneline", f"origin/{branch}..HEAD"])
            else:
                unpushed = run_command(["git", "log", "--oneline", "HEAD"])

            if unpushed.strip():
                info("No new changes to commit, but found unpushed commits.")
                git_push(branch)
            else:
                info("Working tree is clean and already up to date with remote.")
                return
        except GitCommandError:
            git_push(branch)
    
    banner("SYNC COMPLETE. REMOTE AND LOCAL ARE ALIGNED.", "ALL CHANGES SAVED AND PUBLISHED.")
