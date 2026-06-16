from pygitgo.utils.executor import run_command
from pygitgo.exceptions import GitCommandError

def git_stash_push(label="GitGo Auto-Stash", loading_msg="Saving your changes...", ok_text=None):
    if not ok_text:
        ok_text = "Changes saved."
    try:
        result = run_command(
            ["git", "stash", "push", "-u", "-m", label],
            loading_msg=loading_msg,
            ok_text=ok_text
        )

        if isinstance(result, str) and "No local changes to save" in result:
            return False
        
        return True

    except GitCommandError:
        return False
    

def git_stash_pop(loading_msg="Restoring your saved changes...", ok_text=None):
    if not ok_text:
        ok_text = "Changes restored."
    try:
        run_command(
            ["git", "stash", "pop"], 
            loading_msg=loading_msg,
            ok_text=ok_text
        )
        return True
    except GitCommandError:
        return False


def git_stash_apply(stash_id=None, loading_msg="Applying saved changes...", ok_text=None):
    if not ok_text:
        ok_text = "Changes applied."
    command = ["git", "stash", "apply"]
    if stash_id is not None:
        command.append(f"stash@{{{stash_id}}}")

    try:
        run_command(command, loading_msg=loading_msg, ok_text=ok_text)
        return True
    except GitCommandError:
        return False


def git_stash_drop(stash_id=None, loading_msg="Cleaning up stash...", ok_text=None):
    if not ok_text:
        ok_text = "Stash cleaned up."
    command = ["git", "stash", "drop"]
    if stash_id is not None:
        command.append(f"stash@{{{stash_id}}}")

    try:
        run_command(command, loading_msg=loading_msg, ok_text=ok_text)
        return True
    except GitCommandError:
        return False

def git_stash_list(loading_msg="Fetching stash list...", ok_text=None):
    if not ok_text:
        ok_text = "Stash list fetched."
    try:
        return run_command([
            "git", "stash", "list",
            "--date=format:%Y-%m-%d %H:%M:%S",
            "--pretty=%gd||%cd||%s"
        ], loading_msg=loading_msg, ok_text=ok_text)
    except GitCommandError:
        return ""

def git_stash_clear(loading_msg="Clearing all stashes...", ok_text=None):
    if not ok_text:
        ok_text = "All stashes cleared."
    try:
        run_command(["git", "stash", "clear"], loading_msg=loading_msg, ok_text=ok_text)
        return True
    except GitCommandError:
        return False
