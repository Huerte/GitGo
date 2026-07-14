from pygitgo.utils.cli_io import info, warning, error, banner
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command
from pygitgo.commands.git_core import abort_pull_conflict
from pathlib import Path
import os
import subprocess
from yaspin import yaspin

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
    
    spinner = yaspin(text="Finishing sync...", color="cyan")
    spinner.start()
    
    # We use subprocess directly here to inject GIT_EDITOR=true. 
    # This completely bypasses Vim/Nano so the user doesn't get trapped 
    # in an editor trying to write a merge commit message.
    env_copy = os.environ.copy()
    env_copy["GIT_EDITOR"] = "true"
    
    result = subprocess.run(
        ["git", "rebase", "--continue"],
        capture_output=True,
        text=True,
        env=env_copy
    )
    
    if result.returncode != 0:
        spinner.fail("✖")
        stderr = result.stderr.strip() or result.stdout.strip()
        if "must edit all merge conflicts" in stderr.lower() or "still have unmerged paths" in stderr.lower():
            raise GitGoError(
                "You still have unresolved conflicts.\n"
                "Open your editor, fix all the conflict markers, save, and then run 'gitgo resolve' again."
            )
        raise GitGoError(f"Resolve failed: {stderr}")
        
    spinner.ok("✔")
    banner("CONFLICT RESOLVED. SYNC COMPLETE.", "YOUR CHANGES AND REMOTE CHANGES ARE MERGED.")
