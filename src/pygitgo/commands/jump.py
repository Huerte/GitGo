from pygitgo.utils.cli_io import warning, info, success, error, confirm, banner, write
from pygitgo.commands.git_branch import (
    is_branch_exist, get_current_branch, git_new_branch, get_main_branch,
)
from pygitgo.commands.stash import (
    git_stash_pop, git_stash_push, git_stash_apply, git_stash_drop
)
from pygitgo.exceptions import GitCommandError, GitGoError
from pygitgo.utils.executor import run_command
import sys


def undo_jump_operation(original_branch, stashed_code, created_branch=None):
    if created_branch:
        run_command(["git", "checkout", original_branch], loading_msg=f"Jumping you back to the original branch '{original_branch}'...")
        try:
            ok_text = None if stashed_code else f"Canceled safely. Back on '{original_branch}'."
            run_command(["git", "branch", "-D", created_branch], loading_msg=f"Removing the empty branch '{created_branch}'...", ok_text=ok_text)
        except GitCommandError:
            warning(f"Could not delete branch '{created_branch}'. Remove it manually with: git branch -D {created_branch}")
    else:
        run_command(["git", "reset", "--hard", "HEAD"], loading_msg="Canceling... Putting your files back exactly how they were...", ok_text="Files restored to original state.")
        ok_text = None if stashed_code else f"Canceled safely. Back on '{original_branch}'."
        run_command(['git', 'checkout', original_branch], loading_msg=f"Jumping you back to the original branch '{original_branch}'...", ok_text=ok_text)

    if stashed_code:
        pop_result = git_stash_pop(ok_text=f"Canceled safely. Back on '{original_branch}'. Your code is safe.")
        if not pop_result:
            warning("Could not restore your unsaved changes automatically. Run 'gitgo state list' to recover them.")


def _jump_interrupt_cleanup(original_branch, stashed_code, created_branch):
    try:
        run_command(["git", "rebase", "--abort"], loading_msg="Aborting in-progress rebase...", ok_text="Rebase aborted.")
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
        pop_result = git_stash_pop(ok_text="Your stashed changes have been restored.")
        if not pop_result:
            warning("Could not restore stash automatically. Run 'gitgo state list' to find it.")
    else:
        success("No git state was changed. Your files are safe.")


def jump_operation(args):
    target_branch = args.branch
    original_branch = get_current_branch(safe=True)

    if original_branch == target_branch:
        warning(f"Already on branch '{target_branch}'.")
        return

    try:
        has_changes = run_command(["git", "status", "--porcelain"], loading_msg="Checking for local changes...")
    except GitCommandError as e:
        stderr = getattr(e, "stderr", str(e))
        if "not a git repository" in stderr.lower():
            raise GitGoError("Not inside a git repository. Run 'gitgo init' or 'gitgo link' first.")
        raise GitGoError(f"Could not check repository status: {stderr}")

    stashed_code = False
    created_branch = None

    try:
        if has_changes.strip():
            stash_result = git_stash_push(label="GitGo Jump Auto-Stash", loading_msg="Auto-saving local changes before switching...")
            if not stash_result:
                from pathlib import Path
                lock_file = Path(".git/index.lock")
                if lock_file.exists():
                    warning("A stale lock file is blocking git.")
                    info(f"Delete this file and try again: {lock_file.absolute()}")
                elif Path(".git/rebase-merge").exists() or Path(".git/rebase-apply").exists():
                    warning("A rebase is in progress. Finish or abort it first.")
                    info("Abort with:  gitgo resolve --abort")
                else:
                    warning("Could not auto-save changes before switching.")
                    info("Run:  git status   to see what is blocking the stash.")
                raise GitGoError("Jump aborted: could not save local changes.")
            stashed_code = True

        if not is_branch_exist(target_branch):
            write()
            warning(f"Branch '{target_branch}' does not exist.")
            if not confirm(f"Create '{target_branch}' and switch to it? (y/n): "):
                info("Jump canceled.")
                if stashed_code:
                    pop_result = git_stash_pop(loading_msg="Restoring your local changes...")
                    if not pop_result:
                        warning("Could not restore changes automatically. Run 'gitgo state list' to recover them.")
                return

            ok_text = f"Branch '{target_branch}' created." if stashed_code else f"On '{target_branch}'."
            git_new_branch(target_branch, ok_text=ok_text)
            created_branch = target_branch
        else:
            run_command(
                ["git", "checkout", target_branch],
                loading_msg=f"Switching to '{target_branch}'...",
                ok_text=f"Switched to '{target_branch}'."
            )
            main_branch = get_main_branch()
            try:
                run_command(
                    ["git", "pull", "--rebase", "--autostash", "origin", main_branch],
                    loading_msg=f"Syncing '{target_branch}' with latest from '{main_branch}'...",
                    ok_text=f"'{target_branch}' is up to date with '{main_branch}'."
                )
            except GitCommandError as e:
                stderr = getattr(e, "stderr", str(e))
                if "conflict" in stderr.lower() or "rebase in progress" in stderr.lower():
                    warning(f"Sync from '{main_branch}' hit a conflict.")
                    info("Fix the conflict files, then run:  gitgo resolve")
                    info("Or cancel the jump with:  gitgo resolve --abort")
                else:
                    warning(f"Could not sync from '{main_branch}': no remote or no internet.")
                    info(f"On '{target_branch}', but not yet synced with '{main_branch}'.")

        if stashed_code:
            apply_result = git_stash_apply(loading_msg="Restoring your local changes...")
            if not apply_result:
                write()
                error("CONFLICT: Your local changes clash with the target branch.")
                write()
                info("Option [Y]: Stay here and fix the conflict lines in your files.")
                info("Option [N]: Undo the switch and go back to where you started.")
                write()
                if not confirm("Fix the conflicts yourself? (y = stay / n = go back): "):
                    undo_jump_operation(original_branch, stashed_code, created_branch)
                    return
                else:
                    write()
                    success(f"On '{target_branch}'. Fix the conflict markers in your files.")
                    warning("Your stash backup is still saved. Run 'gitgo state list' to see it.")
                    return
            else:
                drop_result = git_stash_drop(loading_msg="Cleaning up temporary stash...", ok_text=f"On '{target_branch}'. Your changes came with you.")
                if not drop_result:
                    warning("Could not clean up the temporary stash. Run 'gitgo state list' to remove it manually.")

        if not getattr(args, "nested", False):
            banner("WORKSPACE RE-POSITIONED. TARGET DEPLOYMENT SECURED.", "ON TARGET BRANCH WITH RE-APPLIED STATE.")
        return

    except KeyboardInterrupt:
        write()
        warning("Jump interrupted (Ctrl+C).")
        _jump_interrupt_cleanup(original_branch, stashed_code, created_branch)
        sys.exit(130)

