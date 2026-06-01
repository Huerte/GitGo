from pygitgo.commands.git_operations import (
    git_new_branch, git_commit, git_push, get_current_branch, is_branch_exist
)
from pygitgo.commands.staging import get_changed_files, display_file_picker, selective_stage
from pygitgo.commands.jump import jump_operation
from pygitgo.utils.config import get_config
from pygitgo.utils.executor import run_command
from pygitgo.utils.colors import info, warning, error, print_banner
from pygitgo.exceptions import GitCommandError, GitGoError
from argparse import Namespace


def push_operation(args):
    branch = args.branch
    message = args.message
    select = args.select if hasattr(args, 'select') else False

    if args.new:
        if not branch:
            raise GitGoError("\nBranch name required when using --new flag!\n")
        git_new_branch(branch)
    else:
        if branch and not message and not is_branch_exist(branch):
            message = branch
            branch = get_current_branch()
            info(f"No branch name provided. Using current branch: '{branch}'\n")
            
        elif branch and is_branch_exist(branch):
            current_branch = get_current_branch()
            if current_branch != branch:
                warning(f"You are currently on branch '{current_branch}', not '{branch}'.")
                user_choice = input(f"Do you want to switch to branch '{branch}'? (y/n): ").lower()
                if user_choice != 'y':
                    raise GitGoError("\nPush aborted to prevent committing to the wrong branch.\n")
                jump_operation(Namespace(branch=branch))
    
        elif not branch:
            branch = get_current_branch()

    if not message:
        message = get_config("default-message", "New Project Update")
        info(f"No commit message provided. Using default: '{message}'\n")

    if select:
        files = get_changed_files()
        if not files:
            info("\nWorking tree is clean. Nothing to select.")
            warning("Make some changes first before using GitGo to commit and push.")
            return

        selected = display_file_picker(files)
        if not selected:
            info("\nNo files selected. Push aborted.\n")
            return

        selective_stage(selected)
        commit_made = git_commit(message, loading_msg="Commiting selected files...", skip_staging=True)
        
        if commit_made:
            git_push(branch)
        
    else:
        commit_made = git_commit(message)
        
        if commit_made:
            git_push(branch)
        else:
            try:
                unpushed = run_command(["git", "log", "--oneline", f"origin/{branch}..HEAD"], loading_msg="Checking for unpushed commits...")

                if unpushed.strip():
                    warning("\nNo changes to commit, but found unpushed commits. Pushing to remote...")
                    git_push(branch)
                else:
                    info("\nWorking tree is clean and everything is up to date.")
                    warning("Make some changes first before using GitGo to commit and push.")
                    return
                
            except (GitCommandError, Exception):
                warning("\nNo changes to commit. Cannot verify remote status.")
                warning("Make some changes first or check your git remote configuration.")
                return

    print_banner("MISSION COMPLETE. ALL TARGETS COMMITTED AND PUSHED.")
