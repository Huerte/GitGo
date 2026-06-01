from pygitgo.commands.git_operations import get_current_branch
from pygitgo.utils.colors import success, warning, error, info
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command


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
            loading_msg=f"Downloading latest updates for '{branch}' (auto-saving your code)..."
        )

        success(f"Project is up to date with '{branch}'.")

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
