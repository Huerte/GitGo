from pygitgo.commands.git_operations import (
    is_branch_exist, get_current_branch, git_new_branch, get_main_branch
)
from pygitgo.utils.executor import run_command
from pygitgo.commands.state import *
from pygitgo.utils.colors import warning, info, success, error
import subprocess
import sys

def jump_operations_help():
    warning("\nJump Operations Help:\n")
    info("Usage: gitgo jump [branch]\n")
    info("Arguments:")
    info("  branch   The name of the branch to jump to.\n")

def undo_jump_operation(original_branch, has_changes):
    if not has_changes.strip():
        run_command(['git', 'checkout', original_branch], loading_msg=f"Jumping you back to the original branch '{original_branch}'...")
        success(f"\nOkay! You are back to the original branch '{original_branch}'.")
        sys.exit(0)

    run_command(["git", "reset", "--hard", "HEAD"], loading_msg="Canceling... Putting your files back exactly how they were...")
    run_command(['git', 'checkout', original_branch], loading_msg=f"Jumping you back to the original branch '{original_branch}'...")
    run_command(["git", "stash", "pop"], loading_msg="Restoring your unsaved changes...")
    success(f"\nCanceled safely!")
    success(f"You are back on your original branch '{original_branch}', and your code is totally safe.\n")

def jump_operation(arguments):  
    if len(arguments) == 0 or arguments[0] in ("-h", "--help", "help"):
        jump_operations_help()
        sys.exit(0)

    target_branch = arguments[0]

    original_branch = get_current_branch().strip()
    
    if original_branch == target_branch:
        warning(f"\nYou are already on branch '{target_branch}'.\n")
        sys.exit(0)

    has_changes = run_command(['git', 'status', '--porcelain'], allow_fail=True)
    if isinstance(has_changes, subprocess.CalledProcessError):
        warning("\nUnable to check for uncommitted changes. Please ensure you're in a valid git repository.")
        sys.exit(1)
    
    stashed_code = False
    if has_changes.strip():
        info("\nYou have unsaved changes here.")
        user_input = input("Do you want to move these changes to your new branch? (y/n): ").strip().lower()
        if user_input != 'y':
            warning("\nOkay! Leaving your changes here. Jumping without them...\n")
        else:
            stash_result = run_command(["git", "stash", "push", "-m", "GitGo Jump Auto-Stash"], allow_fail=True, loading_msg="Saving your changes before jumping...")
            if isinstance(stash_result, subprocess.CalledProcessError):
                warning("\nFailed to save your changes. Please resolve any issues and try again.")
                sys.exit(1)
            info("\nYour changes have been saved. Jumping to the new branch...")
            stashed_code = True
            
    if not is_branch_exist(target_branch):
        warning(f"\nBranch '{target_branch}' does not exist.\n")
        user_input = input("Do you want to create it and jump to it? (y/n): ").strip().lower()

        if user_input != 'y':
            info("Exiting without jumping...\n")
            if stashed_code:
                run_command(["git", "stash", "pop"], loading_msg="Putting your unsaved changes back...")
            sys.exit(0)
        
        git_new_branch(target_branch)
    else:
        run_command(['git', 'checkout', target_branch], loading_msg=f"Moving you to branch '{target_branch}'...")

    main_branch = get_main_branch()
    get_origin_updates = run_command(['git', 'pull', 'origin', main_branch], allow_fail=True, loading_msg=f"Downloading the latest updates from '{main_branch}'...")
    
    if isinstance(get_origin_updates, subprocess.CalledProcessError):
        warning(f"\nFailed to pull updates from '{main_branch}'. Make sure you have internet or the remote branch exists.")
        user_input = input("Do you want to stay on the new branch without the latest updates? (y/n): ").strip().lower()
        if user_input != 'y':
            undo_jump_operation(original_branch, has_changes if stashed_code else "")
            sys.exit(1)
        else:
            success(f"\nOkay! You are on the new branch, but without the latest updates from '{main_branch}'.")

    if stashed_code:
        apply_result = run_command(['git', 'stash', 'apply'], allow_fail=True, loading_msg="Unpacking your unsaved changes...")
        if isinstance(apply_result, subprocess.CalledProcessError):
            error("\nSTOP! There is a 'Merge Conflict'.")
            warning("Your unsaved code clashes with the new code from 'main'.\n")
            info("Option [Y]: Stay here and fix the red conflict lines yourself.")
            info("Option [N]: Cancel everything and go back to normal.\n")
            conflict_choice = input("Do you want to fix it yourself? (y/n): ").strip().lower()

            if conflict_choice != 'y':
                undo_jump_operation(original_branch, has_changes)
                sys.exit(0)
            else:
                success("\nOkay! You are on the new branch with your code.")
                warning("Please open your code editor RIGHT NOW to fix the conflicts!\n")
                run_command(["git", "stash", "drop"], allow_fail=True, loading_msg="Cleaning up the temporary stash...")
                sys.exit(0)
        else:
            run_command(["git", "stash", "drop"], allow_fail=True, loading_msg="Cleaning up the temporary stash...")
            success(f"\nSuccess! You are now on '{target_branch}'.")
            success("Your unsaved code was moved here safely!\n")
            sys.exit(0)
    else:
        success(f"\nSuccess! You are now on '{target_branch}'.\n")
        sys.exit(0)

