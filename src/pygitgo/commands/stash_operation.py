from pygitgo.utils.executor import command_failed, run_command


def git_stash_push(label="GitGo Auto-Stash", loading_msg="Saving your changes..."):
    result = run_command(
        ["git", "stash", "push", "-u", "-m", label],
        allow_fail=True,
        loading_msg=loading_msg
    )
    if command_failed(result):
        return False
    if isinstance(result, str) and "No local changes to save" in result:
        return False
    return True

def git_stash_pop(loading_msg="Restoring your saved changes..."):
    result = run_command(
        ["git", "stash", "pop"], 
        allow_fail=True, 
        loading_msg=loading_msg
    )
    return not command_failed(result)

def git_stash_apply(stash_id=None, loading_msg="Applying saved changes..."):
    command = ["git", "stash", "apply"]
    if stash_id is not None:
        command.append(f"stash@{{{stash_id}}}")

    result = run_command(command, allow_fail=True, loading_msg=loading_msg)
    return not command_failed(result)

def git_stash_drop(stash_id=None, loading_msg="Cleaning up stash..."):
    command = ["git", "stash", "drop"]
    if stash_id is not None:
        command.append(f"stash@{{{stash_id}}}")

    result = run_command(command, allow_fail=True, loading_msg=loading_msg)
    return not command_failed(result)

def git_stash_list(loading_msg="Fetching stash list..."):
    return run_command([
        "git", "stash", "list",
        "--date=format:%Y-%m-%d %H:%M:%S",
        "--pretty=%gd||%cd||%s"
    ], allow_fail=True, loading_msg=loading_msg)

def git_stash_clear(loading_msg="Clearing all stashes..."):
    result = run_command(["git", "stash", "clear"], allow_fail=True, loading_msg=loading_msg)
    return not command_failed(result)
