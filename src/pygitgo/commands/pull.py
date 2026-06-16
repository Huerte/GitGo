from pygitgo.commands.git_branch import get_current_branch
from pygitgo.utils.colors import success, warning, error, info
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command
from pathlib import Path
import sys


def _pull_interrupt_cleanup():
    rebase_in_progress = (
        Path(".git/rebase-merge").exists() or
        Path(".git/rebase-apply").exists()
    )

    if rebase_in_progress:
        warning("A rebase is in progress from the interrupted pull.")
        try:
            run_command(["git", "rebase", "--abort"], loading_msg="Aborting interrupted rebase...", ok_text="Rebase aborted. Branch is back to its pre-pull state.")
        except GitCommandError:
            error("Could not abort rebase automatically.")
            info("Run manually: git rebase --abort")
    else:
        success("No partial rebase detected. Branch is clean.")

    try:
        stash_list = run_command(["git", "stash", "list"])
        if stash_list and "autostash" in stash_list.lower():
            info("An autostash entry was found. Your local changes are safe.")
            info("Run 'gitgo state list' to find it, then 'gitgo state load <id>' to restore it.")
    except GitCommandError:
        pass


def pull_operation(args):
    branch = args.branch

    if not branch:
        branch = get_current_branch()
        info(f"No branch provided. Pulling latest updates for '{branch}'...")

    try:
        try:
            run_command(["git", "ls-remote", "--heads", "origin", branch])
        except GitCommandError:
            error(f"Branch '{branch}' does not exist on the remote.")
            info("Push your local branch first, or verify the branch name.")
            raise GitGoError("Pull aborted — branch not found on remote.")

        run_command(
            ["git", "pull", "--rebase", "--autostash", "origin", branch],
            loading_msg=f"Downloading latest updates for '{branch}' (auto-saving your code)...",
            ok_text=f"Project is up to date with '{branch}'."
        )

    except KeyboardInterrupt:
        print()
        warning("Pull interrupted (Ctrl+C).")
        _pull_interrupt_cleanup()
        sys.exit(130)

    except GitCommandError as e:
        error_msg = str(e).lower()
        if "conflict" in error_msg or "rebase in progress" in error_msg:
            error("MERGE CONFLICT DETECTED!")
            print()
            info("1. Open your code editor.")
            info("2. Fix the conflict lines in your files.")
            info("3. Save the files.")
            info("4. Run:  git rebase --continue")
            print()
            raise GitGoError("Pull failed — resolve conflicts to continue.")
        else:
            raise GitGoError(f"Failed to pull from remote: {e}")
