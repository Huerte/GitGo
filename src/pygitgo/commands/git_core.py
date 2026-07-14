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
    except GitCommandError as e:
        stderr = getattr(e, "stderr", str(e))
        if "not a git repository" in stderr.lower():
            raise GitGoError("Not inside a git repository. Run 'gitgo init' or 'gitgo link' first.")
        raise GitGoError(f"Could not check repository status: {stderr}")
    
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
        stderr = getattr(e, "stderr", str(e))
        if "rebase in progress" in stderr.lower():
            handle_rebase()
        elif "non-fast-forward" in stderr.lower() or "rejected" in stderr.lower():
            info("The remote has commits you don't have locally.")
            info("Run 'gitgo pull' first, then push again.")
            raise GitGoError("Push rejected: pull the latest changes first.")
        elif "repository not found" in stderr.lower() or "does not exist" in stderr.lower():
            info("Run:  git remote -v   to verify the remote URL.")
            raise GitGoError("Push failed: remote repository not found.")
        elif "permission denied" in stderr.lower():
            info("Check that your SSH key is added to GitHub.")
            info("Run:  gitgo user login   to re-authenticate.")
            raise GitGoError("Push failed: permission denied.")
        else:
            info("Run:  git remote -v   to inspect your current remote.")
            raise GitGoError(f"Push failed: {stderr}" if stderr else "Push failed — check the output above.")


def abort_pull_conflict():
    from pathlib import Path
    from pygitgo.utils.cli_io import warning, info, confirm
    from pygitgo.exceptions import GitCommandError, GitGoError
    from pygitgo.utils.executor import run_command
    from pygitgo.commands.git_branch import get_current_branch
    
    rebase_in_progress = Path(".git/rebase-merge").exists() or Path(".git/rebase-apply").exists()
    
    if rebase_in_progress:
        warning("A sync or jump hit a merge conflict and is paused.")
        if not confirm("Cancel the sync and discard any conflict fixes? (y/n): ", destructive=True):
            info("Canceled. The conflict is still active.")
            return False
            
        try:
            run_command(["git", "rebase", "--abort"], loading_msg="Aborting sync...", ok_text="Sync aborted. Branch is back to how it was before the conflict.")
            return True
        except GitCommandError as e:
            raise GitGoError(f"Abort failed: {getattr(e, 'stderr', str(e))}")

    try:
        run_command(["git", "rev-parse", "ORIG_HEAD"])
    except GitCommandError:
        raise GitGoError(
            "No pull to undo. ORIG_HEAD not found — this means no pull has been run yet."
        )

    try:
        branch = get_current_branch(safe=True)
    except GitCommandError as e:
        raise GitGoError(f"Could not determine the current branch: {e}")

    warning("This will reset your branch to the state before the last pull.")
    warning("Any commits that arrived in the pull will be removed locally.")
    if not confirm("Undo the last pull? Type 'y' to confirm: ", destructive=True):
        info("Canceled. Branch is unchanged.")
        return False

    try:
        run_command(
            ["git", "reset", "--hard", "ORIG_HEAD"],
            loading_msg="Reverting to pre-pull state...",
            ok_text="Branch reset to its state before the last pull."
        )
    except GitCommandError as e:
        raise GitGoError(f"Undo failed: {getattr(e, 'stderr', str(e))}")

    try:
        behind = run_command(["git", "rev-list", "--count", f"HEAD..origin/{branch}"]).strip()
        if behind and int(behind) > 0:
            warning(f"Your local branch is now {behind} commit(s) behind remote '{branch}'.")
            info("The remote still has the pulled commits. Your local copy has been reset.")
            info(f"To push your undo to the remote: git push --force origin {branch}")
            info("Only do this if you are the only person working on this branch.")
    except (GitCommandError, ValueError):
        pass

    return True
