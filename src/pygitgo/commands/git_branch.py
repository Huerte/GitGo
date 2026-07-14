from pygitgo.utils.cli_io import warning, error, info, confirm
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command
from pygitgo.utils.config import get_config
from argparse import Namespace


def get_current_branch(safe=False):
    branch = run_command(["git", "branch", "--show-current"]).strip()
    if not branch:
        # We are in a detached HEAD state.
        commit_hash = run_command(["git", "rev-parse", "--short", "HEAD"]).strip()
        
        if safe:
            warning("You are in a 'detached HEAD' state (not on any branch).")
            warning("If you switch away now, your current commits could be lost.")
            if confirm("Would you like to create a new branch here to save your work? (y/n): "):
                new_branch = input("Enter a name for the new branch: ").strip()
                if new_branch:
                    run_command(["git", "checkout", "-b", new_branch])
                    return new_branch
            raise GitGoError("Operation aborted to prevent data loss in detached HEAD state.")
            
        return commit_hash
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


def git_new_branch(branch, ok_text=None):
    try:
        if not ok_text:
            ok_text = f"Branch '{branch}' created."
        run_command(["git", "checkout", "-b", branch], loading_msg=f"Creating branch '{branch}'...", ok_text=ok_text)
    except GitCommandError:
        try:
            current = get_current_branch()
        except Exception:
            current = ""

        if current == branch:
            info(f"Already on branch '{branch}'. Continuing...")
        else:
            error(f"Failed to create branch '{branch}'. It may already exist.")
            if confirm(f"Switch to the existing branch '{branch}' instead? (y/n): "):
                from pygitgo.commands.jump import jump_operation
                jump_operation(Namespace(branch=branch))
            else:
                raise GitGoError(f"Operation canceled. Branch '{branch}' already exists.")

    return branch
