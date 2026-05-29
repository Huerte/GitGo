from pygitgo.exceptions import GitGoError
from pygitgo.utils.colors import success, warning, error, info
from pygitgo.utils.executor import run_command
from pygitgo.exceptions import GitCommandError
from pygitgo.commands.git_operations import get_current_branch
import subprocess
import sys

def pull_operation(args):
    branch = args.branch

    if not branch:
        branch = get_current_branch()
        info(f"No branch provided. Pulling latest updates for '{branch}'...\n")

    try:
        remote_refs = run_command(["git", "ls-remote", "--heads", "origin", branch], allow_fail=True)
        if isinstance(remote_refs, subprocess.CalledProcessError) or not remote_refs.strip():
            error(f"\nFailed! The branch '{branch}' does not exist on the remote server.")
            warning("You might need to push your local branch first.\n")
            raise GitGoError()

        run_command(
            ["git", "pull", "--rebase", "--autostash", "origin", branch], 
            loading_msg=f"Downloading latest updates for '{branch}' (auto-saving your code)..."
        )
        
        success(f"\nSuccess! Your project is now up to date with '{branch}'.\n")

    except GitCommandError as e:
        error_msg = str(e).lower()
        if "conflict" in error_msg or "rebase in progress" in error_msg:
            error("\nMERGE CONFLICT DETECTED!")
            warning("Your local code clashes with the new code downloaded from the server.\n")
            info("1. Open your code editor down below.")
            info("2. Fix the red conflict lines in your files.")
            info("3. Save the files.")
            info("4. Run this command to finish:  git rebase --continue\n")
            raise GitGoError()
        else:
            raise GitGoError(
                "\nFailed to pull updates from the server!"
                "Please check your internet connection and try again."
                f"Details: {e}\n"
            )
