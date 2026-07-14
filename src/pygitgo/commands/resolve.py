from pygitgo.utils.cli_io import info, warning, error, banner
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command
from pygitgo.commands.git_core import abort_pull_conflict
from pathlib import Path

def resolve_operation(args):
    if getattr(args, 'abort', False):
        abort_pull_conflict()
        return

    rebase_in_progress = Path(".git/rebase-merge").exists() or Path(".git/rebase-apply").exists()
    if not rebase_in_progress:
        raise GitGoError("No conflict resolution is currently in progress. You are good to go!")
        
    try:
        run_command(["git", "status", "--porcelain"])
    except GitCommandError:
        raise GitGoError("Not inside a git repository.")
        
    # Stage the resolved files
    run_command(["git", "add", "."], loading_msg="Staging resolved files...", ok_text="Conflict fixes staged.")
    
    try:
        run_command(
            ["git", "rebase", "--continue"],
            loading_msg="Finishing sync...",
            extra_env={"GIT_EDITOR": "true"}
        )
    except GitCommandError as e:
        stderr = getattr(e, "stderr", str(e))
        if "must edit all merge conflicts" in stderr.lower() or "still have unmerged paths" in stderr.lower():
            raise GitGoError(
                "You still have unresolved conflicts.\n"
                "Open your editor, fix all the conflict markers, save, and then run 'gitgo resolve' again."
            )
        raise GitGoError(f"Resolve failed: {stderr}")
        
    banner("CONFLICT RESOLVED. SYNC COMPLETE.", "YOUR CHANGES AND REMOTE CHANGES ARE MERGED.")
