from pygitgo.commands.git_branch import (
    is_branch_exist, get_current_branch, git_new_branch, get_main_branch,
)
from pygitgo.commands.stash import (
    git_stash_pop, git_stash_push, git_stash_apply, git_stash_drop
)
from pygitgo.utils.colors import warning, info, success, error
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command
import sys


def undo_jump_operation(original_branch, stashed_code, created_branch=None):
    if created_branch:
        run_command(["git", "checkout", original_branch], loading_msg=f"Jumping you back to the original branch '{original_branch}'...")
        try:
            run_command(["git", "branch", "-D", created_branch], loading_msg=f"Removing the empty branch '{created_branch}'...")
        except GitCommandError:
            warning(f"Could not delete branch '{created_branch}'. Remove it manually with: git branch -D {created_branch}")
    else:
        run_command(["git", "reset", "--hard", "HEAD"], loading_msg="Canceling... Putting your files back exactly how they were...")
        run_command(['git', 'checkout', original_branch], loading_msg=f"Jumping you back to the original branch '{original_branch}'...")

    if stashed_code:
        pop_result = git_stash_pop()
        if not pop_result:
            warning("Could not restore your unsaved changes automatically. Run 'gitgo state list' to recover them.")

    print()
    success(f"Canceled safely.")
    success(f"Back on '{original_branch}'. Your code is safe.")


def _jump_interrupt_cleanup(original_branch, stashed_code, created_branch):
    try:
        run_command(["git", "rebase", "--abort"])
        info("In-progress rebase aborted.")
    except GitCommandError:
        pass

    try:
        current_branch = get_current_branch()
    except Exception:
        current_branch = original_branch

    if current_branch != original_branch:
        try:
            undo_jump_operation(original_branch, stashed_code, created_branch)
        except GitCommandError:
            warning(f"Could not auto-revert. You are on '{current_branch}'.")
            warning(f"Run manually: git checkout {original_branch}")
            if stashed_code:
                warning("Then restore your stash: git stash pop")
    elif stashed_code:
        pop_result = git_stash_pop()
        if pop_result:
            success("Your stashed changes have been restored.")
        else:
            warning("Could not restore stash automatically. Run 'gitgo state list' to find it.")
    else:
        success("No git state was changed. Your files are safe.")


def jump_operation(args):
    target_branch = args.branch
    original_branch = get_current_branch()

    if original_branch == target_branch:
        warning(f"Already on branch '{target_branch}'.")
        return

    try:
        has_changes = run_command(['git', 'status', '--porcelain'], loading_msg="Checking for uncommitted changes...")
    except GitCommandError:
        raise GitGoError("Unable to check for uncommitted changes — make sure you're in a valid git repository.")

    stashed_code = False
    created_branch = None

    try:
        if has_changes.strip():
            print()
            info("You have unsaved changes here.")
            user_input = input("Do you want to move these changes to your new branch? (y/n): ").strip().lower()
            if user_input != 'y':
                print()
                warning("You cannot switch branches with unsaved changes. Jump canceled.")
                return
            else:
                stash_result = git_stash_push(label="GitGo Jump Auto-Stash", loading_msg="Saving your changes before jumping...")
                if not stash_result:
                    warning("Stash failed. Your working tree may have untracked files.")
                    info("Run:  git status   to see what's blocking the stash.")
                    raise GitGoError("Jump aborted — could not save working changes.")
                info("Changes saved. Jumping to the new branch...")
                stashed_code = True

        if not is_branch_exist(target_branch):
            print()
            warning(f"Branch '{target_branch}' does not exist.")
            user_input = input("Do you want to create it and jump to it? (y/n): ").strip().lower()

            if user_input != 'y':
                info("Exiting without jumping...")
                if stashed_code:
                    pop_result = git_stash_pop(loading_msg="Putting your unsaved changes back...")
                    if not pop_result:
                        warning("Could not restore your unsaved changes automatically. Run 'gitgo state list' to recover them.")
                return

            git_new_branch(target_branch)
            created_branch = target_branch
        else:
            run_command(['git', 'checkout', target_branch], loading_msg=f"Moving you to branch '{target_branch}'...")

            main_branch = get_main_branch()

            try:
                run_command(['git', 'pull', 'origin', main_branch], loading_msg=f"Downloading the latest updates from '{main_branch}'...")
            except GitCommandError:
                warning(f"Failed to pull updates from '{main_branch}'. No internet, or the remote branch doesn't exist yet.")
                user_input = input("Stay on the new branch without the latest updates? (y/n): ").strip().lower()
                if user_input != 'y':
                    undo_jump_operation(original_branch, stashed_code, created_branch)
                    raise GitGoError("Jump aborted — could not sync with remote.")
                else:
                    info(f"On '{target_branch}', but without the latest updates from '{main_branch}'.")

        if stashed_code:
            apply_result = git_stash_apply(loading_msg="Unpacking your unsaved changes...")
            if not apply_result:
                print()
                error("MERGE CONFLICT — your changes clash with the target branch.")
                print()
                info("Option [Y]: Stay here and fix the conflict lines yourself.")
                info("Option [N]: Cancel everything and go back to where you started.")
                print()
                conflict_choice = input("Do you want to fix it yourself? (y/n): ").strip().lower()

                if conflict_choice != 'y':
                    undo_jump_operation(original_branch, stashed_code, created_branch)
                    return
                else:
                    print()
                    success(f"On '{target_branch}'. Conflict markers are in your files.")
                    warning("Open your editor and fix the conflict lines.")
                    info("Your stash backup is still saved. Run 'gitgo state list' to see it.")
                    return
            else:
                drop_result = git_stash_drop(loading_msg="Cleaning up the temporary stash...")
                if not drop_result:
                    warning("Could not clean up the temporary stash. Run 'gitgo state list' to remove it manually.")
                print()
                success(f"On '{target_branch}'. Your changes came with you.")
                return
        else:
            print()
            success(f"On '{target_branch}'.")
            return

    except KeyboardInterrupt:
        print()
        warning("Jump interrupted (Ctrl+C).")
        _jump_interrupt_cleanup(original_branch, stashed_code, created_branch)
        sys.exit(130)
